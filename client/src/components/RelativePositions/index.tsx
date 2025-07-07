import React from 'react';

import type { Detection } from '../../types';
import RelativePosition from '../RelativePosition';
// import ColorKey from '../ColorKey';
// import { CLASS_COLORS } from '../../utils/colorUtils';

interface RelativePositionsProps {
    positions: { [cameraId:string]: Detection[] };
}

const RelativePositions: React.FC<RelativePositionsProps> = ({ positions }) => {
    if (!positions || Object.keys(positions).length === 0) {
        return null;
    }

    return (
        <div>
            {/* <ColorKey colorMap={CLASS_COLORS} /> */}
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
                {Object.entries(positions).map(([cameraId, positions]) => (
                    <RelativePosition key={cameraId} cameraId={cameraId} positions={positions} />
                ))}
            </div>
        </div>
    );
};

export default RelativePositions; 