import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, AlertCircle, Trash2, RefreshCw, CheckCircle2, ShieldAlert } from 'lucide-react';
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

    // 1. Validate MIME type
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setValidationError(
        `Invalid file type (${file.type || 'unknown'}). Supported formats are JPEG, PNG, and WebP.`
      );
      return;
    }

    // 2. Validate file size
    if (file.size > MAX_SIZE_BYTES) {
      setValidationError(
        `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum allowed size is 15 MB.`
      );
      return;
    }

    // Process valid file
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
        <div className="mb-4 p-3 rounded-xl bg-rose-950/70 border border-rose-800/80 text-rose-200 text-xs flex items-center justify-between animate-fade-in">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{validationError}</span>
          </div>
          <button
            onClick={() => setValidationError(null)}
            className="text-rose-400 hover:text-white text-xs underline ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Hidden Native File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* When No Image is Loaded: Drag & Drop Ingestion Zone */}
      {!activeImage && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-200 p-8 sm:p-12 text-center flex flex-col items-center justify-center ${
            isDragOver
              ? 'border-blue-500 bg-blue-950/30 scale-[1.01]'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/70'
          }`}
        >
          {/* Central Upload Icon */}
          <div className="w-14 h-14 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4 shadow-inner">
            {isUploading ? (
              <RefreshCw className="w-7 h-7 animate-spin text-blue-400" />
            ) : (
              <UploadCloud className="w-7 h-7" />
            )}
          </div>

          <h4 className="text-sm font-semibold text-white">
            {isUploading ? 'Ingesting and validating image...' : 'Upload Tactical or Reconnaissance Image'}
          </h4>
          <p className="text-xs text-slate-400 mt-1 max-w-sm">
            Drag and drop your image file here, or click to browse from local workstation.
          </p>

          <div className="flex items-center space-x-3 mt-4 text-[11px] text-slate-500">
            <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60">
              JPEG, PNG, WebP
            </span>
            <span>•</span>
            <span>Up to 15 MB</span>
            <span>•</span>
            <span className="text-emerald-400 flex items-center space-x-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>100% Local</span>
            </span>
          </div>
        </div>
      )}

      {/* When Image is Loaded: Compact Action Bar */}
      {activeImage && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800 mb-4">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-10 h-10 rounded-lg overflow-hidden border border-slate-700 shrink-0 bg-slate-950">
              <img
                src={activeImage.url}
                alt={activeImage.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="min-w-0">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-white truncate max-w-[200px] sm:max-w-xs">
                  {activeImage.name}
                </span>
                <span className="px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 text-[10px] font-mono">
                  {activeImage.width}×{activeImage.height}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">{activeImage.size}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-1.5 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Replace</span>
            </button>
            <button
              onClick={removeImage}
              className="px-3 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 text-xs font-medium border border-rose-800/60 flex items-center space-x-1.5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Remove</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
