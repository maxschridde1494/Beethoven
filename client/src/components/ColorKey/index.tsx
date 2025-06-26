import React from 'react';

interface ColorKeyProps {
    colorMap: { [key: string]: string };
}

const ColorKey: React.FC<ColorKeyProps> = ({ colorMap }) => {
    return (
        <div style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}>
            <div style={{ textAlign: 'left' }}>Color Key</div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'row', gap: '15px' }}>
                {Object.entries(colorMap).map(([className, color]) => {
                    if (className === 'default') return null;
                    return (
                        <li key={className} style={{ display: 'flex', alignItems: 'center' }}>
                            <div style={{ width: '20px', height: '20px', backgroundColor: color, marginRight: '5px', border: '1px solid #000' }}></div>
                            <span>{className}</span>
                        </li>
                    );
                })}
            </ul>
        </div>
    );
};

export default ColorKey; 