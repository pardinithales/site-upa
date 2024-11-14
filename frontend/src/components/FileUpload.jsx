// C:\Users\fagun\OneDrive\Desktop\indicadores-upa\src\components\FileUpload.jsx

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Upload, FileType, AlertCircle, Loader2 } from 'lucide-react';

const FileUpload = ({ onDataReceived }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [files, setFiles] = useState({ pdf: null, xlsx: null });
  const [dragActive, setDragActive] = useState(false);

  const validateFiles = () => {
    if (!files.pdf || !files.xlsx) {
      setError('Por favor, selecione um arquivo PDF e um arquivo Excel (XLSX).');
      return false;
    }
    return true;
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    processSelectedFiles(droppedFiles);
  };

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files);
    processSelectedFiles(selectedFiles);
  };

  const processSelectedFiles = (selectedFiles) => {
    selectedFiles.forEach(file => {
      if (file.name.toLowerCase().endsWith('.pdf')) {
        setFiles(prev => ({ ...prev, pdf: file }));
      } else if (file.name.toLowerCase().match(/\.(xlsx|xls)$/)) {
        setFiles(prev => ({ ...prev, xlsx: file }));
      }
    });
    setError(null);
  };

  const processFiles = async () => {
    if (!validateFiles()) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('files', files.pdf, 'document.pdf');
    formData.append('files', files.xlsx, 'document.xlsx');

    try {
        const response = await fetch('http://localhost:8001/test-upload/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao processar arquivos');
        }

        const result = await response.json();
        console.log('Upload result:', result); // Log de depuração
        
        if (result.data) {
            onDataReceived(result.data);
            setFiles({ pdf: null, xlsx: null });
        }
    } catch (error) {
        console.error('Upload error:', error); // Logging aprimorado de erros
        setError(error.message);
    } finally {
        setUploading(false);
    }
};

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-6 w-6" />
          Upload de Arquivos
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div
            className={`border-2 ${dragActive ? 'border-primary' : 'border-dashed'} 
                     rounded-lg p-6 text-center relative
                     ${dragActive ? 'bg-primary/10' : 'bg-background'}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".pdf,.xlsx,.xls"
              multiple
              disabled={uploading}
            />
            <div className="flex flex-col items-center gap-2">
              {uploading ? (
                <>
                  <Loader2 className="h-12 w-12 animate-spin text-gray-400" />
                  <span>Processando arquivos...</span>
                </>
              ) : (
                <>
                  <Upload className="h-12 w-12 text-gray-400" />
                  <p className="text-sm text-gray-600">
                    Clique para selecionar ou arraste os arquivos aqui
                  </p>
                  <p className="text-xs text-gray-500">
                    (PDF da UPA e planilha Excel)
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Status dos arquivos */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <FileType className={files.pdf ? "text-green-500" : "text-gray-300"} />
              <span className="text-sm">
                PDF: {files.pdf ? files.pdf.name : "Não selecionado"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <FileType className={files.xlsx ? "text-green-500" : "text-gray-300"} />
              <span className="text-sm">
                Excel: {files.xlsx ? files.xlsx.name : "Não selecionado"}
              </span>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <button
            onClick={processFiles}
            disabled={uploading || !files.pdf || !files.xlsx}
            className="w-full py-2 px-4 bg-primary text-white rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {uploading ? "Processando..." : "Processar Arquivos"}
          </button>
        </div>
      </CardContent>
    </Card>
  );
};

export default FileUpload;
