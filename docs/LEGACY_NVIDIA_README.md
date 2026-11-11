# NVIDIA Multimodal Assistant

A command-line assistant for NVIDIA's OpenAI-compatible multimodal API.

## Setup

1. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Put your NVIDIA API key in `.env`:

   ```text
   NVIDIA_API_KEY=your_real_key
   ```

   Keep `.env` private. It is excluded by `.gitignore`.

## Usage

Ask a text question:

```powershell
python main.py "Explain dependency injection with a practical example"
```

Analyze a local image:

```powershell
python main.py --image "C:\photos\receipt.jpg" "Extract the items and prices"
```

Analyze an image URL:

```powershell
python main.py --image "https://example.com/photo.jpg" "Describe this image"
```

Start a conversation with follow-up questions:

```powershell
python main.py --interactive
```

Use `--no-stream` when a complete response should be printed only after the API finishes.

For faster everyday answers, reduce the reasoning and output budget:

```powershell
python main.py --fast "Explain dependency injection with a practical example in Golang"
```

You can also tune one request directly:

```powershell
python main.py --reasoning-effort low --max-tokens 1024 "Say hello in one sentence"
```

Streaming does not guarantee an immediate first token: the server must finish
request validation, scheduling, and model prefill before it sends the first
event. Therefore, a long delay before `response status=200` is server/model
startup latency, not a Python streaming problem. Use `--fast` for short daily
questions and reserve `reasoning_effort=max` for difficult tasks.

For timeout diagnosis, enable safe request diagnostics:

```powershell
python main.py --debug "Explain dependency injection with a practical example in Golang"
```

Debug output reports connection/response timing, status, content type, and
whether a key is present. It never prints the API key or prompt contents. If
the model takes longer to start responding, increase `NVIDIA_TIMEOUT` in `.env`,
or compare behavior with `--no-stream`.

The timeout is the read timeout used while waiting for NVIDIA's response
headers and subsequent stream data. A message such as
`response-header timeout` means the network connection was established, but
the model did not begin responding before that limit.

## Configuration

The default model is `moonshotai/kimi-k3`. You can override settings in `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `NVIDIA_MODEL` | `moonshotai/kimi-k3` | Model identifier |
| `NVIDIA_MAX_TOKENS` | `4096` | Maximum response length |
| `NVIDIA_TEMPERATURE` | `0.7` | Response creativity, from 0 to 2 |
| `NVIDIA_REASONING_EFFORT` | `max` | Reasoning effort requested from the model |
| `NVIDIA_TIMEOUT` | `120` | Request timeout in seconds |
| `NVIDIA_API_URL` | NVIDIA endpoint | API endpoint override |
