FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


RUN apt-get update && apt-get install -y \
    software-properties-common \
    git \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    wget \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O ngrok-stable-linux-amd64.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip \
    && unzip ngrok-stable-linux-amd64.zip \
    && mv ngrok /usr/local/bin \
    && rm ngrok-stable-linux-amd64.zip

RUN echo "Checking Ngrok installation..." \
    && ngrok --version

WORKDIR /app

RUN echo "Checking CUDA installation..." \
    && nvcc --version

RUN python3.11 -m venv venv
ENV PATH="/app/venv/bin:$PATH"
RUN . venv/bin/activate

COPY . .

ENV CMAKE_ARGS="-DLLAMA_CUDA=on"

RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

RUN chmod +x start.py

EXPOSE 80

CMD ["sh", "-c", "python3 start.py && tail -f /dev/null"]
