import React, { useRef, useEffect } from 'react';
import type { Prediction } from '../../types';
import { getColorForClass } from '../../utils/colorUtils';

interface InitialPredictionProps {
    cameraId: string;
    predictions: Prediction[];
}

const InitialPrediction: React.FC<InitialPredictionProps> = ({ cameraId, predictions }) => {
    const imageRef = useRef<HTMLImageElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const imageUrl = `http://localhost:8000/api/assets/${cameraId}-static.jpg`;

    useEffect(() => {
        const canvas = canvasRef.current;
        const context = canvas?.getContext('2d');
        const image = imageRef.current;

        if (!canvas || !context || !image) {
            return;
        }

        const drawPredictions = () => {
            if (!image) return;
            
            canvas.width = image.clientWidth;
            canvas.height = image.clientHeight;
            
            const scaleX = canvas.width / image.naturalWidth;
            const scaleY = canvas.height / image.naturalHeight;
            
            context.clearRect(0, 0, canvas.width, canvas.height);
            
            predictions.forEach(p => {
                const x = p.x - p.width / 2;
                const y = p.y - p.height / 2;
                
                const color = getColorForClass(p.class);
                context.strokeStyle = color;
                context.lineWidth = 2;
                context.strokeRect(x * scaleX, y * scaleY, p.width * scaleX, p.height * scaleY);
                
                const label = p.confidence.toFixed(2);
                context.font = '10px Arial';
                context.fillStyle = 'black';
                context.fillText(label, x * scaleX, y * scaleY - 5);
            });
        };

        if (image.complete) {
            drawPredictions();
        } else {
            image.onload = drawPredictions;
        }

        window.addEventListener('resize', drawPredictions);

        return () => {
            window.removeEventListener('resize', drawPredictions);
        };

    }, [predictions]);

    return (
        <div style={{ marginBottom: '20px', flexShrink: 0 }}>
            <div style={{ position: 'relative' }}>
                <img ref={imageRef} src={imageUrl} alt={cameraId} style={{ height: '300px', width: 'auto' }} />
                <canvas
                    ref={canvasRef}
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        pointerEvents: 'none',
                    }}
                />
            </div>
            <div>{cameraId}</div>
        </div>
    );
};

export default InitialPrediction; 