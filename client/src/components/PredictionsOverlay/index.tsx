import React, { useEffect, useRef, useState } from 'react';
import type { Detection } from '../../types';
import { getColorForClass } from '../../utils/colorUtils';

interface PredictionsOverlayProps {
    cameraId: string;
    wsUrl: string;
}

const PredictionsOverlay: React.FC<PredictionsOverlayProps> = ({ cameraId, wsUrl }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [predictions, setPredictions] = useState<Detection[]>([]);

    useEffect(() => {
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log(`[${cameraId}] WebSocket connected`);
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.data?.detections?.[0]?.camera_id === cameraId) {
                setPredictions(message.data.detections);
            }
        };

        ws.onclose = () => {
            console.log(`[${cameraId}] WebSocket disconnected`);
        };

        ws.onerror = (error) => {
            console.error(`[${cameraId}] WebSocket error:`, error);
        };

        return () => {
            ws.close();
        };
    }, [cameraId, wsUrl]);

    useEffect(() => {
        const canvas = canvasRef.current;
        const context = canvas?.getContext('2d');
        if (!canvas || !context) return;

        const video = canvas.parentElement?.querySelector('video');
        if (video) {
            canvas.width = video.clientWidth;
            canvas.height = video.clientHeight;
        }

        context.clearRect(0, 0, canvas.width, canvas.height);

        predictions.forEach(p => {
            const x = p.x - p.width / 2;
            const y = p.y - p.height / 2;
            
            const scaleX = canvas.width / 640;
            const scaleY = canvas.height / 480;

            const color = getColorForClass(p.class_name);
            context.strokeStyle = color;
            context.lineWidth = 4;
            context.strokeRect(x * scaleX, y * scaleY, p.width*scaleX, p.height*scaleY);
            
            const label = p.note_name && p.key_number
                ? `${p.note_name} (${p.key_number}) | ${(p.confidence * 100).toFixed(0)}%`
                : `${p.class_name} ${(p.confidence * 100).toFixed(0)}%`;
            const fontSize = 16;
            context.font = `${fontSize}px Arial`;
            
            const textWidth = context.measureText(label).width;
            context.fillStyle = color;
            context.fillRect(x*scaleX, y*scaleY - fontSize, textWidth + 8, fontSize + 4)

            context.fillStyle = "white";
            context.fillText(label, x * scaleX + 4, y * scaleY - 2);
        });

    }, [predictions]);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: 'none',
            }}
        />
    );
};

export default PredictionsOverlay; 