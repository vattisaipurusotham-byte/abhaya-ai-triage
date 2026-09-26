# 1. Use a lightweight official Python 3.10 image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the dependencies file and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your entire project (main.py) into the container
COPY . .

# 5. Expose the port that FastAPI runs on
EXPOSE 8000

# 6. Command to boot up the Uvicorn server when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]