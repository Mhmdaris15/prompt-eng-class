import json
import unittest
from unittest.mock import patch, Mock
import tempfile
from pathlib import Path
import numpy as np
from .pipeline import parse_embedding, unit_matrix, make_context, make_prompt, prepare, DEFAULT_RUN, read, CourseAPI
from .config import EXPECTED_DIM, MY_RAG_INSTRUCTION

class VectorAndEvidenceTests(unittest.TestCase):
    def test_rejects_invalid_vectors(self):
        for value in ['[1, 2]', json.dumps([0]*EXPECTED_DIM), json.dumps([float('nan')]*EXPECTED_DIM)]:
            with self.subTest(value=value[:12]), self.assertRaises(ValueError): parse_embedding(value)

    def test_cosine_is_scale_invariant_and_distinguishes_orthogonal_vectors(self):
        docs=unit_matrix([[3,0],[0,7]])
        np.testing.assert_allclose(docs @ unit_matrix([5,0]),[1,0])

    def test_zero_query_is_rejected(self):
        with self.assertRaises(ValueError): unit_matrix([0,0])

    def test_context_keeps_full_abstract_and_leading_zero_identifier(self):
        p={'title':'Sample','authors':'A','article_id':'0704.0140','abstract':'a'*2500}
        context=make_context([p]); self.assertIn('[S1]',context); self.assertIn('0704.0140',context); self.assertIn('a'*2500,context)
        self.assertIn(MY_RAG_INSTRUCTION,make_prompt('Question',[p]))

    def test_prepared_real_corpus_matches_manifest(self):
        m=prepare(); papers=read(DEFAULT_RUN/'corpus.json'); matrix=np.load(DEFAULT_RUN/'vectors.npy',allow_pickle=False)
        self.assertEqual(matrix.shape,(len(papers),EXPECTED_DIM)); self.assertEqual(m['selected'],100)
        self.assertEqual(len({p['article_id'] for p in papers}),100)
        self.assertTrue(all(isinstance(p['article_id'],str) and p['article_id'].startswith('0') for p in papers))

    def test_course_chat_uses_provider_prefix_and_marks_truncation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ',{},clear=True):
            env=Path(tmp)/'.env'; env.write_text('AICLAB_API_KEY=test-course-key\n',encoding='utf-8')
            api=CourseAPI(env)
            response=Mock(ok=True); response.json.return_value={'choices':[{'message':{'content':'partial'},'finish_reason':'length'}]}
            with patch('lab3.pipeline.requests.post',return_value=response) as post:
                result=api.chat('anthropic/claude-haiku-4.5','Question')
                self.assertEqual(post.call_args.kwargs['json']['model'],'cloud/anthropic/claude-haiku-4.5')
                self.assertEqual(post.call_args.kwargs['headers']['Authorization'],'Bearer test-course-key')
                self.assertEqual(result['status'],'truncated')

    def test_course_embedding_uses_distinct_header_and_matching_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ',{},clear=True):
            env=Path(tmp)/'.env'; env.write_text('COURSE_API_KEY=test-course-key\n',encoding='utf-8')
            response=Mock(status_code=200); response.json.return_value={'data':[{'embedding':[1.0]*EXPECTED_DIM}]}
            with patch('lab3.pipeline.requests.post',return_value=response) as post:
                vector=CourseAPI(env).embedding('Question')
                self.assertEqual(vector.shape,(1024,))
                self.assertEqual(post.call_args.kwargs['json']['model'],'cloud-bge/BAAI/bge-m3')
                self.assertEqual(post.call_args.kwargs['headers']['x-bf-vk'],'test-course-key')
                self.assertNotIn('Authorization',post.call_args.kwargs['headers'])

if __name__=='__main__': unittest.main()
