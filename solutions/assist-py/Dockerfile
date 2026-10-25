# 1.  
FROM python:3.11-slim

# 2.
LABEL maintainer="vychik@lab.local"
LABEL version="1.0"

# 3.    
WORKDIR /app

# 4.   
COPY requirements.txt .

# 5.   Python
RUN pip install -r requirements.txt

# 6.       
COPY app/ ./app/

# 7.    
EXPOSE 5493

# 8.  FastAPI-  uvicorn   
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5493"]
