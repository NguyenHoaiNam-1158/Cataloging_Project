from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Backend API")

@app.get("/")
def read_root():
    return {"message": "Backend server is running successfully!"}

if __name__ == "__main__":
    # Lệnh này sẽ chạy server ở port 8000 và giữ cho container luôn sống
    uvicorn.run(app, host="0.0.0.0", port=8000)