
// Server URLs
// Replace these URLs with your own server URLs
// You can use a service like ngrok to create a secure tunnel to your local server
// Example: ngrok http 5000 which I used to create the URLs below
// Replace the URLs below with your own ngrok URLs
// Currently these links aren't permanent it will expire if I shut down the ngrok server

const SYNC_URL = "https://7141-122-187-117-179.ngrok-free.app/sync_from_sheet";
const DELETE_URL = "https://7141-122-187-117-179.ngrok-free.app/delete_row";

// Function to initialize the previousIDs list
function initializeIDs() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const range = sheet.getRange(1, 1, sheet.getLastRow(), 1);  
  const previousIDs = range.getValues().flat();  
  Logger.log(`Initial IDs: ${previousIDs}`);
  
  PropertiesService.getScriptProperties().setProperty('previousIDs', JSON.stringify(previousIDs));
}

// Sync row to the server
function syncRowToServer(e) {
  if (!e) {
    Logger.log("Event object is undefined");
    return;
  }

  const sheet = e.source.getActiveSheet();
  const range = e.range;
  const row = range.getRow();
  const col = range.getColumn();

  if (col < 2) return; 

  const rowData = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  Logger.log(`Row Data: ${JSON.stringify(rowData)}`);

  const rowObject = {
    "ID": rowData[0],    
    "Name": rowData[1],  
    "Age": rowData[2],   
    "Email": rowData[3]  
  };

  const options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(rowObject)
  };
  
  UrlFetchApp.fetch(SYNC_URL, options);
}

// Delete a row from the server
function deleteRowFromServer(rowID) {
  const options = {
    "method": "delete",
    "muteHttpExceptions": true
  };

  const url = `${DELETE_URL}?ID=${rowID}`;  
  const response = UrlFetchApp.fetch(url, options);
  
  Logger.log(`Delete URL: ${url}`);
  Logger.log(`Server response: ${response.getContentText()}`);
}

// Trigger for detecting changes
function onChange(e) {
  const sheet = e.source.getActiveSheet();
  const currentIDs = sheet.getRange(1, 1, sheet.getLastRow(), 1).getValues().flat();  
  const previousIDs = JSON.parse(PropertiesService.getScriptProperties().getProperty('previousIDs') || '[]');
  
  Logger.log(`Current IDs in onChange: ${currentIDs}`);
  Logger.log(`Previous IDs before change detection: ${previousIDs}`);

  const deletedIDs = previousIDs.filter(id => !currentIDs.includes(id));

  if (deletedIDs.length > 0) {
    deletedIDs.forEach(rowID => {
      Logger.log(`Row deletion detected. Deleted ID: ${rowID}`);
      deleteRowFromServer(rowID);
    });
  }

  PropertiesService.getScriptProperties().setProperty('previousIDs', JSON.stringify(currentIDs));
  Logger.log(`Updated IDs after onChange: ${currentIDs}`);
}

// Trigger when the sheet is edited
function atEdit(e) {
  const range = e.range;
  const sheet = e.source.getActiveSheet();
  
  if (range.getColumn() >= 2) {
    syncRowToServer(e);
  }
}

// Add this to the onOpen function to initialize IDs when the sheet opens
function onOpen() {
  Logger.log("Spreadsheet opened. Initializing IDs.");
  initializeIDs();
}

function doPost(e) {
  try {
    // Parse the incoming JSON data
    var data = JSON.parse(e.postData.contents);

    var operation = data.operation;

    if (!operation) {
      return ContentService.createTextOutput(JSON.stringify({
        status: 'error',
        message: 'No operation specified.'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var range = sheet.getDataRange();
    var values = range.getValues();

    var id = data.ID;
    var rowIndex = -1;
    for (var i = 1; i < values.length; i++) {
      if (values[i][0] == id) {
        rowIndex = i + 1; 
        break;
      }
    }

    if (operation === 'insert' || operation === 'update') {
      if (rowIndex !== -1) {
        // Update existing row
        sheet.getRange(rowIndex, 1, 1, values[0].length).setValues([[
          data.ID,
          data.Name,
          data.Age || '',
          data.Email
        ]]);
      } else {
        // Append new row
        sheet.appendRow([ 
          data.ID,
          data.Name,
          data.Age || '',
          data.Email
        ]);
      }
    } else if (operation === 'delete') {

      const sheet = e.source.getActiveSheet();
      const currentIDs = sheet.getRange(1, 1, sheet.getLastRow(), 1).getValues().flat();

      if (rowIndex !== -1) {
        if(currentIDs.includes(rowIndex)){
          sheet.deleteRow(rowIndex);
        }
        else{
          return {"result":"Nothing to delete"};
        }
      } else {
        return {"result":"Nothing to delete"};
      }
    } else {
      return ContentService.createTextOutput(JSON.stringify({
        status: 'error',
        message: 'Invalid operation.'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: 'success',
      message: 'Data processed successfully.'
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: error.message
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

