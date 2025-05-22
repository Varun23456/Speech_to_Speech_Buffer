"""Configuration settings for the RabbitMQ service, ASR API, and Machine Translation API."""

CLOUDAMQP_URL = "amqps://keqzgbzz:ooZR8GlQRTtXg6V__RBZd0leDtVYZhrj@puffin.rmq2.cloudamqp.com/keqzgbzz"
INPUT_LANG = "english"
OUTPUT_LANG = "hindi"
GENDER = "male"

ASR_API_TIMEOUT = 60
MT_API_TIMEOUT = 60 
TTS_API_TIMEOUT = 60

ASR_DICTIONARY = {
    "english": {
        "api_endpoint": "https://canvas.iiit.ac.in/sandboxbeprod/infer_asr/67127dcbb1a6984f0c5e7d35",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjdjYmYwNjQzYTc4OTE2NTI3M2M0OTRhIiwibW9kZWxfaWQiOiI2NzEyN2RjYmIxYTY5ODRmMGM1ZTdkMzUiLCJyZXF1ZXN0c19wZXJfbWludXRlIjoxMDAwLCJhY2Nlc3Nfc3RhcnRfZGF0ZSI6IjIwMjUtMDMtMDlUMDA6MDA6MDAiLCJhY2Nlc3NfZW5kX2RhdGUiOiIyMDI2LTAzLTA5VDIzOjU5OjU5IiwiaGFzaGVkX3Bhc3N3b3JkIjoiJDJiJDEyJGF6OHdvWlJYWnBRNVQvOFF5OEhjbi55YzhmUkRhSldTRmVhenMxaEc5bXJEWnlZNEI3QzNxIiwiZXhwIjoxNzczMTAwNzk5fQ.ejLV8yV2n0e_sMvdWmXLMwmYbCQ4_22-2hnzCi4X_UA"
    },
}

MT_DICTIONARY = {
    "english_to_hindi": {
        "api_endpoint": "https://canvas.iiit.ac.in/sandboxbeprod/check_model_status_and_infer/66ff6446186aeed166f4d943",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjdjYmYwNjQzYTc4OTE2NTI3M2M0OTRhIiwibW9kZWxfaWQiOiI2NmZmNjQ0NjE4NmFlZWQxNjZmNGQ5NDMiLCJyZXF1ZXN0c19wZXJfbWludXRlIjoxMDAwLCJhY2Nlc3Nfc3RhcnRfZGF0ZSI6IjIwMjUtMDMtMDlUMDA6MDA6MDAiLCJhY2Nlc3NfZW5kX2RhdGUiOiIyMDI2LTAzLTA5VDIzOjU5OjU5IiwiaGFzaGVkX3Bhc3N3b3JkIjoiJDJiJDEyJGF6OHdvWlJYWnBRNVQvOFF5OEhjbi55YzhmUkRhSldTRmVhenMxaEc5bXJEWnlZNEI3QzNxIiwiZXhwIjoxNzczMTAwNzk5fQ.6SwzYvAebm2fEAS6uYuqVX53leHs287r4v5Coi9wLNA"
    },
}

TTS_DICTIONARY = {
    "hindi": {
        "api_endpoint": "https://canvas.iiit.ac.in/sandboxbeprod/generate_tts/67bca89ae0b95a6a1ea34a92",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjdjYmYwNjQzYTc4OTE2NTI3M2M0OTRhIiwibW9kZWxfaWQiOiI2N2JjYTg5YWUwYjk1YTZhMWVhMzRhOTIiLCJyZXF1ZXN0c19wZXJfbWludXRlIjoxMDAwLCJhY2Nlc3Nfc3RhcnRfZGF0ZSI6IjIwMjUtMDMtMDlUMDA6MDA6MDAiLCJhY2Nlc3NfZW5kX2RhdGUiOiIyMDI2LTAzLTA5VDIzOjU5OjU5IiwiaGFzaGVkX3Bhc3N3b3JkIjoiJDJiJDEyJGF6OHdvWlJYWnBRNVQvOFF5OEhjbi55YzhmUkRhSldTRmVhenMxaEc5bXJEWnlZNEI3QzNxIiwiZXhwIjoxNzczMTAwNzk5fQ.9a2_LRSNVpWxNFCJeCA6tReMXQgKra2EHQKEipJPjn0"
    },
}
