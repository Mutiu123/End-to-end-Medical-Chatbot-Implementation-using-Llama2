# End-to-end-Medical-Chatbot-Implementation-using-Llama2

### Prerequisites
- Python 3.8 or higher
- Flask
- Hugging Face Transformers
- Pinecone
- Llama 2 model files
- Kubernetes
- AWS 

# How to run?
### STEPS:

Clone the repository

```bash
Project repo: https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2.git
```

### STEP 01- Create a conda environment after opening the repository

```bash
conda create -n medicalChatBot python=3.8 -y
```

```bash
conda activate medicalChatBot
```

### STEP 02- install the requirements
```bash
pip install -r requirements.txt
```

### Download used model
llama-2-7b-chat.ggmlv3.q4_0.bin

## From the following link:
https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/tree/main



### Create a `.env` file in the root directory and add your Pinecone credentials as follows:

```ini
PINECONE_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
PINECONE_API_ENV = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

```bash
# run the following command
python store_index.py
```

```bash
# Finally run the following command
python app.py
```

Now,
```bash
open up localhost:
```

```bash
enter  localhost:8080
```

## Screenshots

![Screenshot demo1](https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2/blob/main/demo/demo1.png)

![Screenshot demo2](https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2/blob/main/demo/demo2.png)

![Screenshot demo3](https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2/blob/main/demo/demo3.png)




