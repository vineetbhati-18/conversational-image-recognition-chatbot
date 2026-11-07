/**
 * Client-Side Image Pre-processor for BEL Conversational Image Recognition.
 * 
 * Downscales oversized client images (e.g. 10MB phone camera shots) in the browser
 * to max 1024x1024 JPEG before network transmission.
 * 
 * Benefits:
 * - Reduces network upload payload by 95% (e.g. from 8MB to ~150KB)
 * - Drastically eliminates latency and network timeouts
 * - Prevents cloud memory exhaustion on Render Free 512MB RAM containers
 */

export async function compressImageForUpload(file, maxDimension = 800, quality = 0.80) {
  if (!file || !file.type.startsWith('image/')) {
    return file;
  }

  // If already under 150KB, skip client resizing
  if (file.size <= 150 * 1024) {
    return file;
  }

  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onerror = () => resolve(file); // Fallback to raw file on error
    reader.onload = (e) => {
      const img = new Image();
      img.onerror = () => resolve(file);
      img.onload = () => {
        let { width, height } = img;

        // If dimensions already fit within maxDimension, use original
        if (width <= maxDimension && height <= maxDimension) {
          resolve(file);
          return;
        }

        if (width > height) {
          if (width > maxDimension) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          }
        } else {
          if (height > maxDimension) {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          resolve(file);
          return;
        }

        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (!blob || blob.size >= file.size) {
              resolve(file);
              return;
            }

            const cleanName = file.name.replace(/\.[^/.]+$/, '') + '.jpg';
            const compressedFile = new File([blob], cleanName, {
              type: 'image/jpeg',
              lastModified: Date.now(),
            });
            resolve(compressedFile);
          },
          'image/jpeg',
          quality
        );
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}
