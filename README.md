# Fantasy Chatbot Layer

A chatbot layer that provides universe-specific conversations with LLM integration. This project allows users to chat with an AI while ensuring all interactions remain within defined fantasy universes. Users can select a specific universe (e.g., Lord of the Rings, The Belgariad) and the system automatically provides context-aware responses.

## Features

- **Universe Selection**: Choose from configured fantasy universes via dropdown
- **Context-Aware Responses**: System automatically adds universe context to queries
- **Topic Validation**: Ensures questions and responses stay within the selected universe
- **Web Interface**: Simple, clean chat interface for interacting with the bot
- **LLM Integration**: Connects to OpenAI-compatible APIs (default: LM Studio at localhost:1234)
- **Configurable Universes**: Easy configuration of universes and their resources via YAML file

## Universes

The following universes are supported (configurable in `config.yaml`):

- Lord of the Rings
- The Silmarillion
- The Belgariad
- Dungeons & Dragons
- Forgotten Realms

## Project Structure

```
fantasy_chatbot/
├── config.yaml              # Configuration file for universes and settings
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
├── web_interface/           # Web interface files
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── services/                # Service modules
│   ├── llm_runner.py        # LLM API integration
│   ├── topic_validator.py   # Topic validation logic
│   └── universe_context.py  # Universe context and query rewriting
└── README.md
```

## Installation

1. **Clone the repository** (if applicable)
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure the application**:
   - Edit `config.yaml` to customize topics and LLM settings
   - Ensure your LLM server is running (default: LM Studio at http://localhost:1234)

## Configuration

Edit `config.yaml` to customize:

```yaml
universes:
  - name: "Lord of the Rings"
    resources:
      - "Middle Earth"
      - "Gandalf"
      - "Frodo Baggins"
      - "The Shire"
      - "Mordor"
      - "Rivendell"
      - "Gollum"
      - "Sauron"
      - "Aragorn"
      - "Legolas"
      - "Gimli"
      - "Hobbits"
      - "Wizards"
      - "Rings of Power"
    system_prompt: "You are a knowledgeable guide through Middle Earth. Answer questions about the Lord of the Rings universe, its characters, places, and lore."

  - name: "The Silmarillion"
    resources:
      - "Valar"
      - "Maiar"
      - "Melkor"
      - "Fëanor"
      - "The Silmarils"
      - "Aulë"
      - "Yavanna"
      - "Morgoth"
      - "Noldor"
      - "Teleri"
      - "First Age"
      - "Tolkien mythology"
    system_prompt: "You are a scholar of Tolkien's mythology. Answer questions about the creation myths, the Valar, and the ancient history of Middle Earth."

  - name: "The Belgariad"
    resources:
      - "Belgarath"
      - "Polgara"
      - "Belgarion"
      - "Dol Goldur"
      - "Riva"
      - "Cthragga"
      - "Angarak"
      - "Witch-king"
      - "Orca"
      - "Alorn"
      - "Witch-Queen"
      - "Polgara's spells"
      - "The Prophecy"
    system_prompt: "You are a historian of the Belgariad universe. Answer questions about the ancient prophecies, the gods, and the history of the Alorn kingdoms."

  - name: "Dungeons & Dragons"
    resources:
      - "D&D"
      - "Dungeons"
      - "Dragons"
      - "Tyr"
      - "Bane"
      - "Lolth"
      - "Drow"
      - "Paladin"
      - "Ranger"
      - "Wizard"
      - "Fighter"
      - "Rogue"
      - "Bard"
      - "Cleric"
      - "Dungeon Master"
      - "AD&D"
      - "5th Edition"
    system_prompt: "You are a Dungeon Master and lore expert. Answer questions about D&D rules, spells, monsters, and the multiverse."

  - name: "Forgotten Realms"
    resources:
      - "Faerûn"
      - "Waterdeep"
      - "Baldur's Gate"
      - "Elminster"
      - "Mystra"
      - "Cormyr"
      - "Shadowrun"
      - "Drizzt Do'Urden"
      - "Beregost"
      - "Icewind Dale"
      - "Silverymoon"
      - "Chult"
      - "Tyranny of Dragons"
      - "Waterdeep: Dragon Heist"
      - "Forgotten Realms wiki"
    system_prompt: "You are a master of Faerûnian lore. Answer questions about the Forgotten Realms setting, its cities, deities, and adventures."

llm:
  api_url: "http://localhost:1234/v1/chat/completions"
  model: "local-model"
  temperature: 0.7
  max_tokens: 500
```

## Usage

### Running the Web Interface

```bash
python main.py
```

Then open your browser and navigate to `http://localhost:8000`

### API Endpoints

- `POST /api/chat` - Send a message to the chatbot
- `GET /api/topics` - Get the list of allowed topics

## How It Works

1. User selects a universe from the dropdown
2. User enters a question in the chat interface
3. System validates the question is related to the selected universe
4. If off-topic, the system politely rejects the question
5. If on-topic, the system rewrites the query to include universe context
6. The rewritten query is sent to the LLM
7. System validates the LLM response is also within the universe
8. Response is presented to the user

## Technology Stack

- **Python 3.10+**
- **LangGraph** - For LLM orchestration
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **OpenAI SDK** - LLM API integration

## License

MIT License