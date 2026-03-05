# Quick Start Guide

Get your Fantasy Chatbot up and running in minutes!

## Prerequisites

- Python 3.10 or higher
- LM Studio (or any OpenAI-compatible LLM server)
- pip (Python package manager)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Your LLM Server

**Using LM Studio:**
1. Download and install LM Studio from https://lmstudio.ai
2. Start LM Studio
3. Select a model (e.g., Llama 3, Mistral, or any local model)
4. Start the server (usually at http://localhost:1234)

**Note:** The chatbot expects the server to be running at `http://localhost:1234/v1/chat/completions`

### 3. Configure the Chatbot

Edit `config.yaml` if needed:

```yaml
# Topics (you can add/remove topics)
topics:
  - "Lord of the Rings"
  - "The Silmarillion"
  - "The Belgariad"
  - "Dungeons and Dragons"
  - "Forgotten Realms"

# LLM settings (adjust if your server is different)
llm:
  api_url: "http://localhost:1234/v1/chat/completions"
  model: "local-model"  # Check your LM Studio model name
```

### 4. Start the Chatbot Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

### 5. Open the Web Interface

Open your browser and navigate to:
```
http://localhost:8000
```

## Testing

### Test 1: Valid Topic
- Ask: "What is the One Ring?"
- Expected: The bot should answer about Lord of the Rings

### Test 2: Off-Topic
- Ask: "What's for dinner tonight?"
- Expected: The bot should politely reject the question

### Test 3: API Testing

You can also test the API directly:

```bash
# Get topics
curl http://localhost:8000/api/topics

# Send a message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Gandalf"}'
```

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### LLM not responding
- Verify LM Studio is running
- Check the API URL in `config.yaml` matches your server's endpoint
- Check LM Studio logs for errors

### Web interface not loading
- Ensure the server is running
- Check browser console for errors
- Try accessing directly: `http://localhost:8000`

### Off-topic messages not being rejected
- Check `config.yaml` topics list
- Adjust `similarity_threshold` if needed
- Verify `use_fuzzy_matching` is set to true

## Customization

### Adding New Topics

Edit `config.yaml`:

```yaml
topics:
  - "New Topic"
  - "Another Topic"
```

### Changing LLM Settings

Adjust in `config.yaml`:

```yaml
llm:
  temperature: 0.7  # Lower = more focused, Higher = more creative
  max_tokens: 500    # Maximum response length
```

### Changing Server Port

Edit `config.yaml`:

```yaml
server:
  port: 9000  # Change to your preferred port
```

## Project Structure

```
fantasy_chatbot/
├── config.yaml              # Configuration file
├── main.py                  # Main application
├── requirements.txt         # Python dependencies
├── services/
│   ├── llm_runner.py        # LLM API integration
│   └── topic_validator.py   # Topic validation
├── web_interface/
│   ├── index.html           # Web interface HTML
│   ├── styles.css           # Web interface styles
│   └── script.js            # Web interface logic
└── README.md                # This file
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize topics and settings in `config.yaml`
- Explore the code in `services/` to understand the implementation
- Add more features as needed!

## Support

For issues or questions, check:
- [README.md](README.md) for detailed documentation
- LM Studio documentation for LLM setup
- Python error messages for troubleshooting

Enjoy chatting with your fantasy chatbot! 🐉