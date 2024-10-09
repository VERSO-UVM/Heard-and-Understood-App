// TODO: Organize
// TODO: Abstract some computation to helper functions
// TODO: Should csv reflect the pause data selected or all data?

const emotionalColor = 'green';
const invitationalColor = 'blue';
const nonConnectiveColor = 'yellow';

const canvasWidth = 500;
const canvasHeight = 300;

const numDataPoints = 75;
const canvasRectWidth = 3;

algorithmButton = document.getElementById("algorithm");
confusionMatrixButton = document.getElementById("confusionMatrix");
rawDataButton = document.getElementById("rawData");

recordingsList = document.getElementById("recordings");
recordingInput = document.getElementById("recordingsInput");

modalPopup = document.getElementById("modalPopup");
background = document.getElementById("modalBackground");
modalContent = document.getElementById("modalContent");

emotionalCheckbox = document.getElementById("emotionalCheckbox");
invitationalCheckbox = document.getElementById("invitationalCheckbox");
nonConnectiveCheckbox = document.getElementById("non-connectiveCheckbox");

showEmotional = true;
showInvitational = true;
showNonConnective = true;

recordingVal = '';

// Arrays of dummy pause data in graph
emotionalPauses = [];
invitationalPauses = [];
nonConnectivePauses = [];

downloadButton = document.getElementById("downloadCSV");

interactiveElements = [algorithmButton, confusionMatrixButton, rawDataButton, emotionalCheckbox, invitationalCheckbox, nonConnectiveCheckbox, downloadButton];

values = ["recording 1", "recording 2", "recording 3", "recording 4"];
datalist = document.getElementById("recordings")
var optionsText = '';
for(i = 0; i < values.length; ++i) {
    optionsText += '<option value="' + values[i] + '" />';
}
datalist.innerHTML = optionsText;

confusionMatrixButton.onclick = function() {
    modalPopup.style.display = "block";
    background.style.display = "block";
    modalContent.textContent = confusionMatrixButton.value + " for " + recordingVal;
}
rawDataButton.onclick = function() {
    modalPopup.style.display = "block";
    background.style.display = "block";
    modalContent.textContent = rawDataButton.value + " for " + recordingVal;
}
recordingsInput.addEventListener("input", function(){
    recordingVal = this.value;
    if (values.includes(recordingVal)) {
        algorithmButton.disabled = false;
    } else {
        algorithmButton.disabled = true;
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

downloadCSV = function() {
    if(recordingVal != ''){
        console.log('downloading csv for ' + recordingVal);
    }
}

window.onclick = function(event) {
    if (event.target == background) {
        modalPopup.style.display = "none";
        background.style.display = "none";
    }
}

function downloadToCSV() {
    if (recordingVal != '') {
        try {
            // let filePath = '../downloadedData/' + recordingVal + '.csv';
            let filePath = recordingVal + '.csv';
            let csvText = generateCSVText();
            const a = document.createElement('a');
            const file = new Blob([csvText], { type: "text/plain" });
            a.href = URL.createObjectURL(file);
            a.download = filePath;
            a.click();
            URL.revokeObjectURL(a.href);

        } catch(error) {
            console.log("Erorr downloading CSV for " + recordingVal)
        }
    }
}

function runAlgorithm() {
    console.log("simulating algorithm...");
    populateGraph();
    interactiveElements.forEach(button=> {
        button.disabled = false;
    })
}

function generateCSVText() {
    let dummyData = ['100101011', '10100101', '1000001000'];
    var returnString = '';
    for (i = 0; i < dummyData.length; ++i) {
        returnString += dummyData[i];
    }
    return returnString;
}

function populateGraph() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    // Emotional pause data
    ctx.fillStyle = emotionalColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        emotionalPauses.push(randomX);
    }
    // Invitational pause data
    ctx.fillStyle = invitationalColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        invitationalPauses.push(randomX);
    }
    // Non-connective pause data
    ctx.fillStyle = nonConnectiveColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        nonConnectivePauses.push(randomX);
    }
}

function isolateData() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");

    // Clear the entire canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if(showEmotional) {
        ctx.fillStyle = emotionalColor;
        for(i = 0; i < emotionalPauses.length; ++i) {
            ctx.fillRect(emotionalPauses[i], 0, canvasRectWidth, canvasHeight);
        }
    }
    if(showInvitational) {
        ctx.fillStyle = invitationalColor;
        for(i = 0; i < invitationalPauses.length; ++i) {
            ctx.fillRect(invitationalPauses[i], 0, canvasRectWidth, canvasHeight);
        }
    }
    if(showNonConnective) {
        ctx.fillStyle = nonConnectiveColor;
        for(i = 0; i < nonConnectivePauses.length; ++i) {
            ctx.fillRect(nonConnectivePauses[i], 0, canvasRectWidth, canvasHeight);
        }
    }
}

function getRandomNumber(min, max) {
    return Math.random() * (max - min) + min;
  }





