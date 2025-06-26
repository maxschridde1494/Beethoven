import React, { useEffect, useRef, useState } from 'react';

interface Prediction {
    x: number;
    y: number;
    width: number;
    height: number;
    confidence: number;
    class_name: string;
}

interface PredictionsOverlayProps {
    cameraId: string;
    wsUrl: string;
}

const PredictionsOverlay: React.FC<PredictionsOverlayProps> = ({ cameraId, wsUrl }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [predictions, setPredictions] = useState<Prediction[]>([]);

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

        // Get the video element to match canvas size
        const video = canvas.parentElement?.querySelector('video');
        if (video) {
            canvas.width = video.clientWidth;
            canvas.height = video.clientHeight;
        }


        context.clearRect(0, 0, canvas.width, canvas.height);
        context.strokeStyle = 'red';
        context.lineWidth = 2;
        context.font = '16px Arial';
        context.fillStyle = 'red';

        predictions.forEach(p => {
            const x = p.x - p.width / 2;
            const y = p.y - p.height / 2;
            
            // a video with resolution 640x480 is scaled to 100% width and auto height
            // so we need to scale the predictions to the canvas size
            const scaleX = canvas.width / 640;
            const scaleY = canvas.height / 480;

            context.strokeRect(x * scaleX, y * scaleY, p.width*scaleX, p.height*scaleY);
            
            const label = `${p.class_name} (${p.confidence.toFixed(2)})`;
            context.fillText(label, x * scaleX, y * scaleY - 5);
        });

    }, [predictions]);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: 'none', // Make canvas transparent to mouse events
            }}
        />
    );
};

export default PredictionsOverlay; 