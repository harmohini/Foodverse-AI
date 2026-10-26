import { useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { Image, Video, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

interface ImageUploadZoneProps {
  onFile: (file: File) => void;
  preview?: string;
  label?: string;
  accept?: Record<string, string[]>;
  maxSizeMB?: number;
  onError?: (msg: string) => void;
}

export function ImageUploadZone({
  onFile,
  preview,
  label = 'Drop your food image here',
  accept = { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'], 'image/webp': ['.webp'] },
  maxSizeMB = 10,
  onError,
}: ImageUploadZoneProps) {
  const onDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      if (rejected.length > 0) {
        const msg = rejected[0]?.errors[0]?.message || 'Invalid file.';
        onError?.(msg);
        return;
      }
      if (accepted[0]) onFile(accepted[0]);
    },
    [onFile, onError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
    maxSize: maxSizeMB * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      id="upload-zone"
      className={clsx(
        'upload-zone rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer min-h-[200px] transition-all duration-200',
        isDragActive && 'drag-active'
      )}
    >
      <input {...getInputProps()} />
      {preview ? (
        <div className="w-full flex flex-col items-center gap-3">
          <img
            src={preview}
            alt="Preview"
            className="max-h-64 rounded-xl object-cover shadow-card"
          />
          <p className="text-sm text-charcoal-100">Click or drop to replace</p>
        </div>
      ) : (
        <>
          <div className="w-14 h-14 rounded-2xl bg-forest-50 flex items-center justify-center mb-4">
            <Image className="w-7 h-7 text-forest-500" />
          </div>
          <p className="font-semibold text-charcoal-900 text-center">{label}</p>
          <p className="text-sm text-charcoal-100 mt-1 text-center">
            or <span className="text-forest-500 font-medium">browse files</span>
          </p>
          <p className="text-xs text-charcoal-100 mt-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            JPEG, PNG, WebP · max {maxSizeMB} MB
          </p>
        </>
      )}
    </div>
  );
}

interface VideoUploadZoneProps {
  onFile: (file: File) => void;
  preview?: string;
  onError?: (msg: string) => void;
}

export function VideoUploadZone({ onFile, preview, onError }: VideoUploadZoneProps) {
  const onDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      if (rejected.length > 0) {
        const msg = rejected[0]?.errors[0]?.message || 'Invalid file.';
        onError?.(msg);
        return;
      }
      if (accepted[0]) onFile(accepted[0]);
    },
    [onFile, onError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/mp4': ['.mp4'], 'video/quicktime': ['.mov'], 'video/webm': ['.webm'] },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      id="video-upload-zone"
      className={clsx(
        'upload-zone rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer min-h-[200px]',
        isDragActive && 'drag-active'
      )}
    >
      <input {...getInputProps()} />
      {preview ? (
        <div className="w-full flex flex-col items-center gap-3">
          <video src={preview} controls className="max-h-48 rounded-xl shadow-card" />
          <p className="text-sm text-charcoal-100">Click or drop to replace</p>
        </div>
      ) : (
        <>
          <div className="w-14 h-14 rounded-2xl bg-forest-50 flex items-center justify-center mb-4">
            <Video className="w-7 h-7 text-forest-500" />
          </div>
          <p className="font-semibold text-charcoal-900">Drop your kitchen video here</p>
          <p className="text-sm text-charcoal-100 mt-1">
            or <span className="text-forest-500 font-medium">browse files</span>
          </p>
          <p className="text-xs text-charcoal-100 mt-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            MP4, MOV, WebM · max 100 MB
          </p>
        </>
      )}
    </div>
  );
}
