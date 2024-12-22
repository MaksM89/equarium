

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('authorization.web:app', port=8081, reload=True)