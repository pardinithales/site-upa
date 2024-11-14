# C:\Users\fagun\OneDrive\Desktop\indicadores-upa\scripts\test_api.py

import asyncio
import sys
import os
import json
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
from contextlib import asynccontextmanager
from datetime import datetime
import pandas as pd

# Importa as funções de extração
from extract_data_both import extract_from_pdf, extract_from_excel

# Configure o loop de eventos no Windows
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://indicadores-upa-front-4p4j6oo23-thales-pardinis-projects.vercel.app/"],  # Substitua "*" pelos domínios específicos, como "http://localhost:3004" e "https://indicadores-upa.vercel.app"
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os headers
)


@asynccontextmanager
async def managed_file_upload(file: UploadFile, timeout=30):
    """Gerencia o ciclo de vida do arquivo temporário com timeout"""
    temp_file = f"temp_{file.filename}"
    try:
        content = await asyncio.wait_for(file.read(), timeout=timeout)
        with open(temp_file, "wb") as f:
            f.write(content)
        yield temp_file
    except asyncio.TimeoutError:
        logger.error(f"Timeout ao processar arquivo {file.filename}")
        raise HTTPException(status_code=408, detail="Timeout ao processar arquivo")
    except Exception as e:
        logger.error(f"Erro ao processar arquivo {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar arquivo")
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.error(f"Erro ao remover arquivo temporário {temp_file}: {e}")

@app.post("/test-upload/")
async def test_upload(files: List[UploadFile] = File(...)):
    """Endpoint para upload de arquivos"""
    try:
        logger.info(f"Recebendo {len(files)} arquivos")
        
        if len(files) != 2:
            raise HTTPException(
                status_code=400,
                detail=f"Envie exatamente 2 arquivos (PDF e Excel). Recebidos: {len(files)}"
            )

        all_data = []
        for file in files:
            logger.info(f"Processando arquivo: {file.filename}")
            
            # Salva arquivo temporariamente
            temp_file = f"temp_{file.filename}"
            try:
                content = await file.read()
                with open(temp_file, "wb") as f:
                    f.write(content)
                
                # Processa baseado na extensão
                if file.filename.lower().endswith('.pdf'):
                    result = extract_from_pdf(temp_file)
                elif file.filename.lower().endswith(('.xlsx', '.xls')):
                    result = extract_from_excel(temp_file)
                else:
                    continue
                
                if result:
                    data = json.loads(result)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        logger.warning(f"Dados inválidos de {file.filename}")
                
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        if not all_data:
            raise HTTPException(
                status_code=422,
                detail="Nenhum dado foi extraído dos arquivos"
            )

        logger.info(f"Total de registros processados: {len(all_data)}")
        return {"status": "success", "data": all_data}

    except Exception as e:
        logger.error(f"Erro ao processar arquivos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivos: {str(e)}"
        )

@app.get("/")
async def read_root():
    return {"message": "API está funcionando"}

@app.on_event("startup")
async def startup_event():
    """Processa os arquivos iniciais na pasta inputs quando o servidor inicia"""
    logger.info("Iniciando processamento inicial dos arquivos")
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'inputs')
    
    if not os.path.exists(input_dir):
        logger.error(f"Diretório de inputs não encontrado: {input_dir}")
        return
    
    all_data = []
    pdf_files = []
    excel_files = []
    
    # Separa arquivos por tipo
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if filename.lower().endswith('.pdf'):
            pdf_files.append(file_path)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            excel_files.append(file_path)
    
    # Processa PDFs
    for pdf_path in pdf_files:
        logger.info(f"Testando PDF: {pdf_path}")
        result = extract_from_pdf(pdf_path)
        if result:
            data = json.loads(result)
            if isinstance(data, list):
                all_data.extend(data)
    
    # Processa Excel
    for excel_path in excel_files:
        logger.info(f"Testando Excel: {excel_path}")
        result = extract_from_excel(excel_path)
        if result:
            data = json.loads(result)
            if isinstance(data, list):
                all_data.extend(data)
    
    # Salva resultado mesclado
    if all_data:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f'merged_data_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dados mesclados salvos em: {output_file}")
        logger.info(f"Total de registros processados: {len(all_data)}")
        
        # Gera estatísticas básicas
        df = pd.DataFrame(all_data)
        stats_file = os.path.join(output_dir, f'merged_stats_{timestamp}.txt')
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("ESTATÍSTICAS DOS DADOS MESCLADOS\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("1. DISTRIBUIÇÃO POR STATUS\n")
            f.write(df['Status'].value_counts().to_string() + "\n\n")
            
            f.write("2. DISTRIBUIÇÃO POR SETOR\n")
            f.write(df['Setor'].value_counts().to_string() + "\n\n")
            
            f.write("3. DISTRIBUIÇÃO POR HOSPITAL\n")
            f.write(df['Hospital'].value_counts().to_string() + "\n")
        
        logger.info(f"Estatísticas salvas em: {stats_file}")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        loop="asyncio",
        http="h11"
    )

