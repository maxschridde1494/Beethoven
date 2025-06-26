export const CLASS_COLORS: { [key: string]: string } = {
    'wh': '#FF0000',      // Red
    'bl': '#0000FF',      // Blue
    'p white': '#FFFF00', // Yellow
    'p black': '#00FF00', // Green
    'default': '#FFFFFF'  // White for any other classes
};

export const getColorForClass = (className: string): string => {
    return CLASS_COLORS[className.toLowerCase()] || CLASS_COLORS['default'];
}; 