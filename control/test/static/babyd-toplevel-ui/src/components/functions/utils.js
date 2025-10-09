export function formatData(data, indentLevel = 0) {
    if (data == null) return ''; // Return empty string for null or undefined
    const indent = '    '; // 4 spaces for indentation
    let formattedData = '';
  
    Object.entries(data).forEach(([key, value]) => {
      const prefix = `${indent.repeat(indentLevel)}${key}: `;
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        formattedData += `${prefix}\n${formatData(value, indentLevel + 1)}`;
      } else if (Array.isArray(value)) {
        const arrayString = value.map(item => JSON.stringify(item)).join(', ');
        formattedData += `${prefix}[${arrayString}]\n`;
      } else {
        formattedData += `${prefix}${JSON.stringify(value)}\n`;
      }
    });
  
    return formattedData;
}
  
export function framesToSeconds(frames) {
const FRAME_RATE = 533000;
return Math.round(frames / FRAME_RATE);
}
  
export function formatTime(totalSeconds) {
const hours = Math.floor(totalSeconds / 3600);
const minutes = Math.floor((totalSeconds % 3600) / 60);
const seconds = totalSeconds % 60;

return [
    hours.toString().padStart(2, '0'),
    minutes.toString().padStart(2, '0'),
    seconds.toString().padStart(2, '0')
].join(':');
}

export const fakeFrameData = {
liveview: {
    frame_data: {
    built: [
        [0,6,11,7,5,0,3,0,2,0,8,0,11,9,5,9],
        [0,0,0,2,0,6,7,7,0,0,4,0,3,0,1,2],
        [0,0,9,9,4,4,0,0,3,0,0,0,10,2,0,0],
        [0,0,0,0,2,8,3,7,0,1,5,0,4,0,9,2],
        [1,5,0,0,0,4,0,1,8,6,3,0,5,7,0,8],
        [1,0,0,5,6,0,3,0,0,4,7,0,0,2,2,6],
        [3,0,0,8,0,0,10,0,0,11,0,2,2,3,0,11],
        [0,5,3,7,8,2,5,0,8,7,2,3,0,0,0,0],
        [0,0,0,0,7,3,0,7,0,0,0,0,0,3,8,3],
        [4,8,1,6,7,5,7,2,0,4,5,3,0,3,0,4],
        [6,2,0,7,0,1,5,4,7,0,0,4,0,0,0,0],
        [1,2,0,7,2,3,7,8,7,0,5,10,0,4,0,0],
        [0,0,0,2,7,11,0,0,0,1,2,10,4,2,0,5],
        [1,0,1,0,0,12,0,0,0,0,4,0,10,0,3,0],
        [0,3,1,3,10,8,8,3,6,3,0,12,3,0,0,0],
        [3,4,0,0,0,7,0,3,0,1,1,0,0,0,6,2]
    ],
    coarse: Array(16).fill(Array(16).fill(0)),
    fine: [
        [0,6,11,7,5,0,3,0,2,0,8,0,11,9,5,9],
        [0,0,0,2,0,6,7,7,0,0,4,0,3,0,1,2],
        [0,0,9,9,4,4,0,0,3,0,0,0,10,2,0,0],
        [0,0,0,0,2,8,3,7,0,1,5,0,4,0,9,2],
        [1,5,0,0,0,4,0,1,8,6,3,0,5,7,0,8],
        [1,0,0,5,6,0,3,0,0,4,7,0,0,2,2,6],
        [3,0,0,8,0,0,10,0,0,11,0,2,2,3,0,11],
        [0,5,3,7,8,2,5,0,8,7,2,3,0,0,0,0],
        [0,0,0,0,7,3,0,7,0,0,0,0,0,3,8,3],
        [4,8,1,6,7,5,7,2,0,4,5,3,0,3,0,4],
        [6,2,0,7,0,1,5,4,7,0,0,4,0,0,0,0],
        [1,2,0,7,2,3,7,8,7,0,5,10,0,4,0,0],
        [0,0,0,2,7,11,0,0,0,1,2,10,4,2,0,5],
        [1,0,1,0,0,12,0,0,0,0,4,0,10,0,3,0],
        [0,3,1,3,10,8,8,3,6,3,0,12,3,0,0,0],
        [3,4,0,0,0,7,0,3,0,1,1,0,0,0,6,2]
    ],
    overflow: Array(16).fill(Array(16).fill(0))
    }
}
};