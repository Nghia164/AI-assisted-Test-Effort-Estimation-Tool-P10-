import google.generativeai as genai

# Thay bằng API Key của bạn
genai.configure(api_key="AIzaSyCX8xU7pfIRhrhY3bQHlG1l5q0UWj4Vfc0")

print("Các model hỗ trợ tạo text (generateContent) cho API Key này:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print("-", m.name)