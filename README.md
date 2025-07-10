# Real-Time Speech-to-Speech Translation Pipeline 

A comprehensive real-time speech translation system that converts speech from one language to another using a microservices architecture with RabbitMQ message queuing. The system processes audio through ASR (Automatic Speech Recognition), MT (Machine Translation), and TTS (Text-to-Speech) services with intelligent buffering and pipeline management.


## Overview

This project implements a real-time speech-to-speech translation pipeline that seamlessly converts English speech to Hindi speech using state-of-the-art AI models. Built with a microservices architecture using RabbitMQ for message queuing, the system ensures low latency, high reliability, and scalable processing.

### Key Objectives
- **Real-Time Processing**: Low-latency speech translation for live conversations
- **Microservices Architecture**: Loosely coupled, scalable service design
- **Pipeline Management**: Intelligent buffering and queue management
- **API Integration**: Integration with Anuvaadhub.io translation services
- **Fault Tolerance**: Robust error handling and recovery mechanisms


### Core Components
- **ASR Service**: Converts speech to text using automatic speech recognition
- **MT Service**: Translates text from source to target language
- **TTS Service**: Converts translated text back to speech
- **Buffer Manager**: Manages audio buffering and playback
- **Message Processors**: Handle RabbitMQ message routing and processing

## Features

### Core Functionality
- **Real-Time Translation**: English to Hindi speech translation
- **Pipeline Processing**: Asynchronous processing through multiple stages
- **Queue Management**: RabbitMQ-based message queuing system
- **Buffer Management**: Intelligent audio buffering for smooth playback
- **Error Handling**: Comprehensive error handling and recovery

### Advanced Features
- **Chunking Support**: Process audio in chunks for streamlined ASR
- **Concurrency Handling**: Support for multiple parallel requests
- **Rate Limiting**: API rate limiting and throttling
- **Logging System**: Comprehensive logging for debugging and monitoring
- **Testing Suite**: Unit, integration, and end-to-end testing

### Technical Features
- **Microservices Architecture**: Loosely coupled service design
- **Event-Driven Processing**: Asynchronous message-based communication
- **API Integration**: Integration with external translation APIs
- **Performance Optimization**: Latency optimization and throughput enhancement
- **Scalability**: Horizontal scaling support

## Installation

### Prerequisites
- **Python** 3.8 or higher
- **RabbitMQ** Server
- **FFmpeg** (for audio processing)
- **API Tokens** for Anuvaadhub.io services

### Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/speech-translation-pipeline.git
cd speech-translation-pipeline/code
```

2. **Create and activate virtual environment:**
```bash
python -m venv myenv
source myenv/bin/activate  # On Linux/Mac
# or
myenv\Scripts\activate     # On Windows
```

3. **Install dependencies:**
```bash
pip install -r req.txt
```

4. **Install and start RabbitMQ:**
```bash
# Ubuntu/Debian
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server

# macOS (using Homebrew)
brew install rabbitmq
brew services start rabbitmq

# Windows - Download from https://www.rabbitmq.com/download.html
```

5. **Configure environment variables:**
```bash
# Create .env file with your configuration
CLOUDAMQP_URL=amqp://localhost
INPUT_LANG=en
OUTPUT_LANG=hi
API_TOKEN=your_anuvaadhub_token
```

## Usage

### Starting the Pipeline

1. **Start RabbitMQ Server:**
```bash
sudo systemctl start rabbitmq-server
```

2. **Start Individual Services:**

**ASR Service:**
```bash
python ASR_service.py
```

**MT Service:**
```bash
python MT_service.py
```

**TTS Service:**
```bash
python TTS_service.py
```

**Buffer Manager:**
```bash
python playbufferaudio.py
```

3. **Generate Test Audio:**
```bash
python Generateaudio.py
```

4. **Push Audio to Pipeline:**
```bash
python ChunksPush.py
```

### Pipeline Flow

1. **Audio Input**: Audio is pushed to the ASR input queue
2. **Speech Recognition**: ASR service converts speech to text
3. **Translation**: MT service translates text to target language
4. **Speech Synthesis**: TTS service converts translated text to speech
5. **Buffer Management**: Audio is buffered and played back
6. **Output**: Translated speech is delivered to the user

## Project Structure

```
code/
├── ASR_API_Manager.py       # ASR service API manager
├── ASR_MT_bridge.py         # Bridge between ASR and MT services
├── ASR_service.py           # ASR microservice implementation
├── Buffer_Manager.py        # Audio buffer management
├── ChunksPush.py           # Audio chunking and queue pushing
├── Config.py               # Configuration management
├── Generateaudio.py        # Test audio generation utility
├── Message_Processor.py    # Base message processing framework
├── MT_API_Manager.py       # MT service API manager
├── MT_service.py           # Machine Translation microservice
├── MT_TTS_bridge.py        # Bridge between MT and TTS services
├── playbufferaudio.py      # Audio playback from buffer
├── req.txt                 # Python dependencies
├── TTS_API_Manager.py      # TTS service API manager
├── TTS_Buffer_bridge.py    # Bridge between TTS and Buffer
├── TTS_service.py          # Text-to-Speech microservice
├── Utils.py                # Utility functions
├── test_endtoend.py        # End-to-end testing
├── test_integration.py     # Integration testing
├── test_unittestASR.py     # ASR unit tests
├── test_unittestBuffer.py  # Buffer unit tests
├── test_unittestMT.py      # MT unit tests
├── test_unittestTTS.py     # TTS unit tests
└── myenv/                  # Python virtual environment
```

## API Integration

### Anuvaadhub.io Services

The system integrates with Anuvaadhub.io for AI model services:

- **ASR Models**: Speech recognition for multiple languages
- **MT Models**: Neural machine translation
- **TTS Models**: High-quality text-to-speech synthesis

### API Authentication
```python
# Configure API tokens in Config.py
API_TOKEN = "your_anuvaadhub_api_token"
BASE_URL = "https://anuvaadhub.io/api"
```

### Service Endpoints
- **ASR**: `/asr/inference`
- **MT**: `/translate`
- **TTS**: `/tts/inference`

## Testing

### Running Tests

**Unit Tests:**
```bash
python test_unittestASR.py
python test_unittestMT.py
python test_unittestTTS.py
python test_unittestBuffer.py
```

**Integration Tests:**
```bash
python test_integration.py
```

**End-to-End Tests:**
```bash
python test_endtoend.py
```

### Test Coverage
- **Unit Tests**: Individual service component testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Complete pipeline testing
- **Performance Tests**: Latency and throughput analysis

## Configuration

### Queue Configuration
```python
# RabbitMQ Queue Names
ASR_INPUT_QUEUE = "asr_input"
ASR_OUTPUT_QUEUE = "asr_output"
MT_INPUT_QUEUE = "mt_input"
MT_OUTPUT_QUEUE = "mt_output"
TTS_INPUT_QUEUE = "tts_input"
TTS_OUTPUT_QUEUE = "tts_output"
BUFFER_QUEUE = "buffer_queue"
LOG_QUEUE = "log_queue"
```

### Language Configuration
```python
# Supported Languages
INPUT_LANG = "en"  # English
OUTPUT_LANG = "hi"  # Hindi
```


## Known Issues and Limitations

### Current Limitations
- **Language Support**: Currently supports English to Hindi translation
- **Audio Format**: Optimized for WAV format at 16kHz
- **Network Dependency**: Requires stable internet for API calls
- **Resource Usage**: Memory intensive for concurrent processing

### Future Enhancements
- **Multi-Language Support**: Additional language pairs
- **Real-Time Streaming**: Continuous audio streaming
- **Mobile Integration**: Mobile app development
