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
    key_number?: number;
    note_name?: string;
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

const BoundingBox: React.FC<BoundingBoxProps> = ({ x, y, width, height, className, confidence, scaleX, scaleY, key_number, note_name }) => {
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
        fontSize: '10px',
        zIndex: getZIndex(className),
        pointerEvents: 'auto',
        textAlign: 'center'
    };

    return (
        <div
            style={boxStyle}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div>
                <div>{note_name}</div>
                <div>{key_number}</div>
                <div>{className}</div>
                <div>{(confidence * 100).toFixed(0)}%</div>
                {/* <div>{isHovered ? `${(confidence * 100).toFixed(0)}%` : className}</div> */}
            </div>
        </div>
    );
};

export default BoundingBox; 