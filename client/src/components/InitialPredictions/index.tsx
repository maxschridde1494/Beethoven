import React from 'react';
import type { Detection } from '../../types';
import InitialPrediction from '../InitialPrediction';
import ColorKey from '../ColorKey';
import { CLASS_COLORS } from '../../utils/colorUtils';

interface InitialPredictionsProps {
    predictions: { [cameraId:string]: Detection[] };
}

const InitialPredictions: React.FC<InitialPredictionsProps> = ({ predictions }) => {
    if (!predictions || Object.keys(predictions).length === 0) {
        return null;
    }

    return (
        <div>
            {/* <ColorKey colorMap={CLASS_COLORS} /> */}
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
                {Object.entries(predictions).map(([cameraId, preds]) => (
                    <InitialPrediction key={cameraId} cameraId={cameraId} predictions={preds} />
                ))}
            </div>
        </div>
    );
};

export default InitialPredictions; 