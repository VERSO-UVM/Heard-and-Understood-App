// TODO: Turn the three arrays of pause data into one
class DataPoint {
    constructor(xStart, xEnd, color) {
        this.xStart = xStart;
        this.xEnd = xEnd;
        this.color = color;
    }

    updateX(xStart, xEnd){
        this.xStart = xStart;
        this.xEnd = xEnd;
    }
}
recordingsList = document.getElementById("recordings");
recordingsInput = document.getElementById("recordingsInput");

const emotionalColor = 'green';
const invitationalColor = 'blue';
const nonConnectiveColor = 'yellow';

const canvasWidth = 500;
const canvasHeight = 300;

const numDataPoints = 75;
const canvasRectWidth = 3;

showEmotional = true;
showInvitational = true;
showNonConnective = true;
showAccuracy = true;

emotionalPauses = [DataPoint];
invitationalPauses = [DataPoint];
nonConnectivePauses = [DataPoint];


emotionalCheckbox = document.getElementById("emotionalCheckbox");
invitationalCheckbox = document.getElementById("invitationalCheckbox");
nonConnectiveCheckbox = document.getElementById("non-connectiveCheckbox");
downloadButton = document.getElementById("downloadCSV");

// accuracyToggle = document.getElementById("accuracyToggle");

recordingVal = '';
recordingLabel = document.getElementById("recordingLabel");
recordings = ["recording 1", "recording 2", "recording 3", "recording 4"];
interactiveElements = [emotionalCheckbox, invitationalCheckbox, nonConnectiveCheckbox, downloadButton];

var optionsText = '';
for(i = 0; i < recordings.length; ++i) {
    optionsText += '<option value="' + recordings[i] + '" />';
}
recordingsList.innerHTML = optionsText;

recordingsInput.addEventListener("input", function(){
    recordingVal = this.value;
    recordingLabel.innerHTML += recordingVal;
    if (recordings.includes(recordingVal)) {
        runAlgorithm()
    } else {
        clearCanvas()
    }
});

emotionalCheckbox.addEventListener("input", function(){
    showEmotional = !showEmotional;
    currentlyVisiblePauses();
    isolateData();
});
invitationalCheckbox.addEventListener("input", function(){
    showInvitational = !showInvitational;
    currentlyVisiblePauses();
    isolateData();
});
nonConnectiveCheckbox.addEventListener("input", function(){
    showNonConnective = !showNonConnective;
    currentlyVisiblePauses();
    isolateData();
});
accuracyToggle.addEventListener("input", function(){
    showAccuracy = !showAccuracy;
    if(showAccuracy){
        console.log("Showing accuracy");
    }
})

// Only for showing that the values are kept track of temporarily
currentlyVisiblePauses = function() {
    if(showEmotional){
        console.log("Showing Emotional Pauses");
    }
    if(showInvitational){
        console.log("Showing Invitational Pauses");
    }
    if(showNonConnective){
        console.log("Showing Non-Connective Pauses");
    }
}

function runAlgorithm() {
    clearCanvas();
    emotionalPauses = [DataPoint];
    invitationalPauses = [DataPoint];
    nonConnectivePauses = [DataPoint];

    console.log("simulating algorithm...");
    populateGraph();
    interactiveElements.forEach(button=> {
        button.disabled = false;
    })
}

function populateGraph() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    // Emotional pause data
    ctx.fillStyle = emotionalColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        if(showEmotional){
            ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        }
        emotionalPauses.push(new DataPoint(randomX, randomX + canvasRectWidth, emotionalColor));
    }
    // Invitational pause data
    ctx.fillStyle = invitationalColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        if(showInvitational){
            ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        }
        invitationalPauses.push(new DataPoint(randomX, randomX + canvasRectWidth, invitationalColor));
    }
    // Non-connective pause data
    ctx.fillStyle = nonConnectiveColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        if(showNonConnective){
            ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        }
        nonConnectivePauses.push(new DataPoint(randomX, randomX + canvasRectWidth, nonConnectiveColor));
    }
}

// function resetPage() {
//     clearCanvas()
//     emotionalPauses = [];
//     invitationalPauses = [];
//     nonConnectivePauses = [];
//     recordingsInput.value = '';
//     interactiveElements.forEach(button=> {
//         button.disabled = true;
//     })
// }

function clearCanvas() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    // Clear the entire canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function isolateData() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    clearCanvas()
    if(showEmotional) {
        ctx.fillStyle = emotionalColor;
        for(i = 0; i < emotionalPauses.length; ++i) {
            ctx.fillRect(emotionalPauses[i].xStart, 0, emotionalPauses[i].xEnd - emotionalPauses[i].xStart, canvasHeight);
        }
    }
    if(showInvitational) {
        ctx.fillStyle = invitationalColor;
        for(i = 0; i < invitationalPauses.length; ++i) {
            ctx.fillRect(invitationalPauses[i].xStart, 0, invitationalPauses[i].xEnd - invitationalPauses[i].xStart, canvasHeight);
        }
    }
    if(showNonConnective) {
        ctx.fillStyle = nonConnectiveColor;
        for(i = 0; i < nonConnectivePauses.length; ++i) {
            ctx.fillRect(nonConnectivePauses[i].xStart, 0, nonConnectivePauses[i].xEnd - nonConnectivePauses[i].xStart, canvasHeight);
        }
    }
}

function getRandomNumber(min, max) {
    return Math.random() * (max - min) + min;
  }


