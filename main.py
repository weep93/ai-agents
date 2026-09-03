from google import genai

client = genai.Client()

try:

    response = client.interactions.create(
        model = "gemini-3.8-flash",
        input = "Write a short poem about the beauty of seeing the world")
    print(response.output_text)
except Exception as e:
    print(f"An error occurred: {e}")



for step in response.step: 
    if step.type == "thought": # if its actually thinkging + matters 
        print("thinking...")
        if step.summary: 
            for content_block in step.summary: 
                if content_block.type == "text":
                    print(content_block.text) # tripple validation its not random ai bullshit


        elif step.type == "model_output": # checks for the actual anwser
            print("model output...")
            if step.summary: 
                for content_block in step.summary: 
                    if content_block.type == "text":
                        print(content_block.text) # tripple validation its not random ai bullshit
