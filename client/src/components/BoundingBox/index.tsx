import React, { useState } from 'react';
import { getColorForClass } from '../../utils/colorUtils';

interface BoundingBoxProps {
    x: number;
    y: number;
    width: number;
    height: number;
    className: string;
    confidence: number;
    scaleX: number;
    scaleY: number;
}

const getZIndex = (className: string) => {
    switch (className.toLowerCase()) {
        case 'bl':
            return 2;
        case 'wh':
            return 1;
        default:
            return 0;
    }
};

const BoundingBox: React.FC<BoundingBoxProps> = ({ x, y, width, height, className, confidence, scaleX, scaleY }) => {
    const [isHovered, setIsHovered] = useState(false);

    const boxStyle: React.CSSProperties = {
        position: 'absolute',
        left: `${(x - width / 2) * scaleX}px`,
        top: `${(y - height / 2) * scaleY}px`,
        width: `${width * scaleX}px`,
        height: `${height * scaleY}px`,
        border: `2px solid ${getColorForClass(className)}`,
        boxSizing: 'border-box',
        color: 'white',
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        fontSize: '6px',
        zIndex: getZIndex(className),
        pointerEvents: 'auto',
    };

    return (
        <div
            style={boxStyle}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {isHovered ? `${(confidence * 100).toFixed(0)}%` : className}
        </div>
    );
};

export default BoundingBox; 