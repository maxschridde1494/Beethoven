import React, { useRef, useState, useEffect } from 'react';
import type { Prediction } from '../../types';
import BoundingBox from '../BoundingBox';

interface InitialPredictionProps {
    cameraId: string;
    predictions: Prediction[];
}

const sortPredictions = (predictions: Prediction[]) => {
    return [...predictions].sort((a, b) => {
        const classA = a.class.toLowerCase();
        const classB = b.class.toLowerCase();
        if (classA === 'bl' && classB !== 'bl') return 1;
        if (classA !== 'bl' && classB === 'bl') return -1;
        return 0;
    });
}

const InitialPrediction: React.FC<InitialPredictionProps> = ({ cameraId, predictions }) => {
    const imageRef = useRef<HTMLImageElement>(null);
    const [imageSize, setImageSize] = useState({ width: 0, height: 0, naturalWidth: 1, naturalHeight: 1 });
    const imageUrl = `http://localhost:8000/api/assets/${cameraId}-static.jpg`;

    const handleImageLoad = () => {
        if (imageRef.current) {
            const { clientWidth, clientHeight, naturalWidth, naturalHeight } = imageRef.current;
            setImageSize({ width: clientWidth, height: clientHeight, naturalWidth, naturalHeight });
        }
    };

    useEffect(() => {
        window.addEventListener('resize', handleImageLoad);
        return () => window.removeEventListener('resize', handleImageLoad);
    }, []);

    const scaleX = imageSize.width / imageSize.naturalWidth;
    const scaleY = imageSize.height / imageSize.naturalHeight;
    const sortedPredictions = sortPredictions(predictions);

    return (
        <div style={{ marginBottom: '20px', flexShrink: 0 }}>
            <div style={{ position: 'relative' }}>
                <img
                    ref={imageRef}
                    src={imageUrl}
                    alt={cameraId}
                    style={{ height: '300px', width: 'auto' }}
                    onLoad={handleImageLoad}
                />
                {sortedPredictions.map(p => (
                    <BoundingBox
                        key={p.detection_id}
                        x={p.x}
                        y={p.y}
                        width={p.width}
                        height={p.height}
                        className={p.class}
                        confidence={p.confidence}
                        scaleX={scaleX}
                        scaleY={scaleY}
                    />
                ))}
            </div>
            <div>{cameraId}</div>
        </div>
    );
};

export default InitialPrediction; 