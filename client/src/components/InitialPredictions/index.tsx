import React from 'react';
import type { Prediction } from '../../types';
import InitialPrediction from '../InitialPrediction';
import ColorKey from '../ColorKey';
import { CLASS_COLORS } from '../../utils/colorUtils';

interface InitialPredictionsProps {
    predictions: { [cameraId:string]: Prediction[] };
}

const InitialPredictions: React.FC<InitialPredictionsProps> = ({ predictions }) => {
    if (!predictions || Object.keys(predictions).length === 0) {
        return null;
    }

    return (
        <div className="card">
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                {Object.entries(predictions).map(([cameraId, preds]) => (
                    <InitialPrediction key={cameraId} cameraId={cameraId} predictions={preds} />
                ))}
                <ColorKey colorMap={CLASS_COLORS} />
            </div>
        </div>
    );
};

export default InitialPredictions; 