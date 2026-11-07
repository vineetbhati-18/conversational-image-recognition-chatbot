import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, Trash2, RefreshCw, Loader2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE_BYTES = 15 * 1024 * 1024; // 15 MB

export default function ImageUploader() {
  const { activeImage, handleImageUpload, removeImage, isUploading } = useChat();
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  const validateAndProcessFile = (file) => {
    setValidationError(null);
    if (!file) return;

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setValidationError(`Unsupported format (${file.type || 'unknown'}). Use JPEG, PNG, or WebP.`);
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      setValidationError(`File exceeds 15 MB (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      return;
    }

    handleImageUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      {/* Validation Error Banner */}
      {validationError && (
        <div className="mb-2 p-2 rounded-lg bg-rose-950/60 border border-rose-800/60 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            <span>{validationError}</span>
          </div>
          <button
            onClick={() => setValidationError(null)}
            className="text-rose-400 hover:text-white text-[11px] ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* When No Image: Elegant Compact Dropzone */}
      {!activeImage && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-xl border border-dashed transition-all p-4 text-center flex items-center justify-center space-x-3.5 ${
            isDragOver
              ? 'border-blue-500 bg-blue-950/20'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/70'
          }`}
        >
          <div className="w-9 h-9 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
            {isUploading ? (
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            ) : (
              <UploadCloud className="w-4 h-4" />
            )}
          </div>
          <div className="text-left min-w-0">
            <p className="text-xs font-medium text-slate-200">
              {isUploading ? 'Uploading and analyzing...' : 'Upload Image'}
            </p>
            <p className="text-[11px] text-slate-500">
              Drop file here or click to browse (JPEG, PNG, WebP up to 15MB)
            </p>
          </div>
        </div>
      )}

      {/* When Image Loaded: Compact Info Bar */}
      {activeImage && (
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <div className="flex items-center space-x-2.5 min-w-0">
            <div className="w-8 h-8 rounded-md overflow-hidden border border-slate-800 shrink-0 bg-slate-950">
              <img
                src={activeImage.url}
                alt={activeImage.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="min-w-0">
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-medium text-slate-200 truncate max-w-[180px] sm:max-w-xs">
                  {activeImage.name}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {activeImage.width}×{activeImage.height}
                </span>
              </div>
              <span className="text-[10px] text-slate-500">{activeImage.size}</span>
            </div>
          </div>

          <div className="flex items-center space-x-1.5 shrink-0">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] flex items-center space-x-1 transition-colors"
              title="Replace image"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Replace</span>
            </button>
            <button
              onClick={removeImage}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-rose-950/70 text-slate-400 hover:text-rose-300 text-[11px] flex items-center space-x-1 transition-colors"
              title="Remove image"
            >
              <Trash2 className="w-3 h-3" />
              <span>Remove</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
