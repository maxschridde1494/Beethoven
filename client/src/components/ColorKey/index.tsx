import React from 'react';

interface ColorKeyProps {
    colorMap: { [key: string]: string };
}

const ColorKey: React.FC<ColorKeyProps> = ({ colorMap }) => {
    return (
        <div style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}>
            <h4>Color Key</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {Object.entries(colorMap).map(([className, color]) => {
                    if (className === 'default') return null;
                    return (
                        <li key={className} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                            <div style={{ width: '20px', height: '20px', backgroundColor: color, marginRight: '10px', border: '1px solid #000' }}></div>
                            <span>{className}</span>
                        </li>
                    );
                })}
            </ul>
        </div>
    );
};

export default ColorKey; 