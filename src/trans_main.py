

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('transaction.web:app', port=8082, reload=True)