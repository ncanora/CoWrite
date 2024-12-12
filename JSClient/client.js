// ================= Client Setup =================
const CLIENT_COLORS = [
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4',
    '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff'
  ];
  
  let clientName = "";
  let clientKey = ""; // Placeholder for future use
  let clients = {}; // {clientName: {color, cursorLocation}}
  let docContent = "";
  let oldContent = "";
  
  let legend = document.getElementById('legend');
  let editorContainer = document.getElementById('editor-container');
  let authContainer = document.getElementById('auth-container');
  let authForm = document.getElementById('auth-form');
  let errorMessage = document.getElementById('error-message');
  
  // ================= WebSocket Setup =================
  let ws;
  
  authForm.addEventListener('submit', function(event) {
      event.preventDefault();
      clientName = document.getElementById('name').value.trim();
      clientKey = document.getElementById('key').value.trim();
  
      if (clientName === "" || clientKey === "") {
          showError("Name and Key are required.");
          return;
      }
  
      connectWebSocket();
  });
  
  function connectWebSocket() {
      ws = new WebSocket("ws://" + window.location.host + "/ws");
  
      ws.onopen = () => {
          console.log("WebSocket connection opened");
          // Send the clientName to the server without the key
          sendMessage({
              command: "NEWCLIENT",
              clientName: clientName
              // Do not send clientKey for now
          });
  
          // Immediately hide auth form and show editor
          authContainer.style.display = "none";
          editorContainer.style.display = "block";
          legend.style.display = "block";
          initializeQuill();
      };
  
      ws.onmessage = (event) => {
          console.log("Message from server:", event.data);
          try {
              const msg = JSON.parse(event.data);
              handleMessage(msg);
          } catch (e) {
              console.error("Error parsing message from server:", e);
          }
      };
  
      ws.onerror = (err) => {
          console.error("WebSocket error:", err);
          showError("WebSocket error. Please try again.");
      };
  
      ws.onclose = (event) => {
          console.log("WebSocket connection closed:", event);
          if (!event.wasClean) {
              showError("WebSocket connection closed unexpectedly. Attempting to reconnect...");
              attemptReconnect();
          } else {
              showError("WebSocket connection closed.");
          }
      };
  }
  
  function attemptReconnect() {
      const reconnectInterval = 3000; // 3 seconds
      const maxReconnectAttempts = 10;
      let reconnectAttempts = 0;
  
      const reconnect = () => {
          if (reconnectAttempts < maxReconnectAttempts) {
              reconnectAttempts++;
              console.log(`Reconnection attempt ${reconnectAttempts}`);
              connectWebSocket();
          } else {
              showError("Unable to reconnect to the server. Please refresh the page.");
          }
      };
  
      setTimeout(reconnect, reconnectInterval);
  }
  
  function sendMessage(msg) {
      if (ws && ws.readyState === WebSocket.OPEN) {
          if (validateOutgoingMessage(msg)) {
              try {
                  ws.send(JSON.stringify(msg));
              } catch (e) {
                  console.error("Failed to send message:", e);
              }
          } else {
              console.warn("Attempted to send invalid message:", msg);
          }
      } else {
          console.warn("WebSocket is not open. Unable to send message:", msg);
      }
  }
  
  function validateOutgoingMessage(msg) {
      if (!msg.command || !msg.clientName) return false;
      switch(msg.command) {
          case 'NEWCLIENT':
              return typeof msg.clientName === 'string' && msg.clientName.trim() !== '';
          case 'ADD':
              return typeof msg.startIndex === 'number' && typeof msg.content === 'string';
          case 'REMOVE':
              return typeof msg.startIndex === 'number' && typeof msg.endIndex === 'number' && msg.endIndex > msg.startIndex;
          case 'CURSOR_MOVE':
              return typeof msg.cursorLocation === 'number';
          case 'PING':
              return true;
          case 'PONG':
              return true;
          default:
              return false;
      }
  }
  
  function showError(message) {
      errorMessage.textContent = message;
      errorMessage.style.display = "block";
  }
  
  // ================= Quill Setup =================
  let quill;
  let cursors;
  
  // Register quill-cursors module with Quill
  Quill.register('modules/cursors', QuillCursors);
  
  function initializeQuill() {
      quill = new Quill('#editor-container', {
          theme: 'snow',
          modules: {
              toolbar: [
                  ['bold', 'italic', 'underline'],
                  ['code-block']
              ],
              cursors: true // Enable the cursors module
          }
      });
  
      cursors = quill.getModule('cursors');
  
      // quill-cursors module loaded
      if (!cursors) {
          console.error("Cursors module not loaded.");
          showError("Failed to load cursor functionalities.");
          return;
      }
  
      // Force newline insertion at doc end (changes the default behavior of Quill)
      quill.keyboard.addBinding({ key: 13 }, (range, context) => {
          if (range.index >= quill.getLength() - 1) {
              quill.insertText(range.index, '\n');
              quill.setSelection(range.index + 1, 0);
              return false;
          }
      });
  
      // Quill Event Handlers
      quill.on('text-change', (delta, oldDelta, source) => {
          if (source !== 'user') {
              oldContent = quill.getText();
              return;
          }
  
          let ops = delta.ops;
  
          let oldPos = 0;
          let newPos = 0;
  
          for (let i = 0; i < ops.length; i++) {
              let op = ops[i];
              if (op.retain) {
                  oldPos += op.retain;
                  newPos += op.retain;
              } else if (op.insert) {
                  let insertedText = op.insert;
                  if (typeof insertedText !== 'string') {
                      console.warn("Invalid insert operation:", op);
                      continue; // Skip invalid inserts
                  }
                  sendMessage({
                      command: "ADD",
                      clientName: clientName,
                      startIndex: newPos,
                      content: insertedText
                  });
                  newPos += insertedText.length;
              } else if (op.delete) {
                  let length = op.delete;
                  if (typeof length !== 'number' || length <= 0) {
                      console.warn("Invalid delete operation:", op);
                      continue; // Skip invalid deletes
                  }
                  sendMessage({
                      command: "REMOVE",
                      clientName: clientName,
                      startIndex: oldPos,
                      endIndex: oldPos + length
                  });
                  oldPos += length;
              }
          }
          oldContent = quill.getText();
      });
  
      quill.on('selection-change', (range, oldRange, source) => {
          if (!range) return;
          let pos = range.index;
          sendMessage({
              command: "CURSOR_MOVE",
              clientName: clientName,
              cursorLocation: pos
          });
      });
  
      // Ping messages (prevents disconnection due to inactivity)
      ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.command === 'PING') {
              sendMessage({ command: 'PONG' });
          } else {
              handleMessage(msg);
          }
      };
  }
  
  // ================= Message Handling =================
  function handleMessage(msg) {
      switch(msg.command) {
          case "NEWCLIENT":
              console.log("NEWCLIENT received:", msg.clientName);
              if (msg.clientName !== clientName) {
                  // Handle new client joining
                  if (!clients[msg.clientName]) {
                      clients[msg.clientName] = {
                          color: assignClientColor(msg.clientName),
                          cursorLocation: -1
                      };
                      console.log(`Added new client: ${msg.clientName}`);
                      updateLegend();
                  }
              }
              break;
          case "DOCUMENT":
              if (quill) {
                  console.log("DOCUMENT received:", msg.content);
                  if (typeof msg.content === 'string') {
                      quill.setText(msg.content);
                      oldContent = quill.getText();
                      quill.setSelection(0, 0);
                  } else {
                      console.warn("Invalid DOCUMENT content:", msg.content);
                  }
              }
              break;
          case "CLIENTS_LIST":
              if (!Array.isArray(msg.clientList)) {
                  console.warn("No clientList received or not an array:", msg.clientList);
                  msg.clientList = [];
              }
              msg.clientList.forEach(cName => {
                  if (cName === clientName) return; // Skip self
                  if (!clients[cName]) {
                      clients[cName] = {
                          color: assignClientColor(cName),
                          cursorLocation: -1
                      };
                      console.log(`Added client to list: ${cName}`);
                  }
              });
              updateLegend();
              break;
          case "ADD":
              console.log("ADD operation:", msg);
              handleAdd(msg);
              break;
          case "REMOVE":
              console.log("REMOVE operation:", msg);
              handleRemove(msg);
              break;
          case "CURSOR_MOVE":
              console.log("CURSOR_MOVE received from", msg.clientName, "at position", msg.cursorLocation);
              if (msg.clientName !== clientName) {
                  // Update remote client's cursor
                  if (!clients[msg.clientName]) {
                      clients[msg.clientName] = {
                          color: assignClientColor(msg.clientName),
                          cursorLocation: msg.cursorLocation
                      };
                      console.log(`Added client for cursor: ${msg.clientName}`);
                  } else {
                      clients[msg.clientName].cursorLocation = msg.cursorLocation;
                  }
                  // Correctly create or update the remote cursor
                  if (cursors) {
                      // Avoid duplicating cursors
                      if (!cursors.cursors[msg.clientName]) {
                          cursors.createCursor(msg.clientName, msg.clientName, clients[msg.clientName].color);
                      }
                      cursors.moveCursor(msg.clientName, { index: msg.cursorLocation, length: 0 });
                  } else {
                      console.warn("Cursors module not initialized.");
                  }
              }
              break;
          case "ERROR":
              console.error("Server Error:", msg.message);
              showError(`Server Error: ${msg.message}`);
              break;
          default:
              console.log("Unknown command:", msg.command);
      }
  }
  
  function handleAdd(msg) {
      let startIndex = msg.startIndex;
      let insertText = msg.content;
  
      console.log("handleAdd: Received ADD message:", msg);
  
      // Validate message fields
      if (typeof startIndex !== 'number' || typeof insertText !== 'string') {
          console.warn("Invalid ADD message received:", msg);
          return;
      }
  
      let currentLength = quill.getLength() - 1;
      console.log(`Quill current length: ${currentLength}, startIndex: ${startIndex}`);
  
      // Validate startIndex
      if (startIndex < 0 || startIndex > currentLength) {
          console.warn("Invalid ADD indices:", msg, currentLength);
          return;
      }
  
      try {
          quill.insertText(startIndex, insertText, 'api'); // 'api' to differentiate from local user changes
          oldContent = quill.getText();
          console.log("Text inserted successfully at", startIndex, ":", insertText);
      } catch (e) {
          console.error("Error inserting text into Quill:", e, "Message:", msg);
      }
  }
  
  function handleRemove(msg) {
      let startIndex = msg.startIndex;
      let endIndex = msg.endIndex;
  
      console.log("handleRemove: Received REMOVE message:", msg);
  
      // Validate message fields
      if (typeof startIndex !== 'number' || typeof endIndex !== 'number') {
          console.warn("Invalid REMOVE message received:", msg);
          return;
      }
  
      let currentLength = quill.getLength() - 1;
      console.log(`Quill current length: ${currentLength}, startIndex: ${startIndex}, endIndex: ${endIndex}`);
  
      // Validate indices
      if (startIndex < 0 || endIndex > currentLength + 1 || startIndex > endIndex) {
          console.warn("Invalid REMOVE indices:", msg, currentLength);
          return;
      }
  
      let length = endIndex - startIndex;
      try {
          quill.deleteText(startIndex, length, 'api'); // 'api' to differentiate from local user changes
          oldContent = quill.getText();
          console.log(`Text deleted successfully from ${startIndex} to ${endIndex}`);
      } catch (e) {
          console.error("Error deleting text from Quill:", e, "Message:", msg);
      }
  }
  
  function updateLegend() {
      legend.innerHTML = "<strong>Editing:</strong> ";
      for (let cName in clients) {
          legend.innerHTML += `<span style="color:${clients[cName].color};">${cName}</span> `;
      }
  }
  
  function assignClientColor(cName) {
      const assigned = Object.values(clients).map(c => c.color);
      let color = CLIENT_COLORS.find(col => !assigned.includes(col));
      if (!color) {
          color = '#' + Math.floor(Math.random() * 16777215).toString(16);
      }
      return color;
  }
  
  // Get a new copy of doc when client failure 
  function requestDocumentFromServer() {
      sendMessage({
          command: "REQUEST_DOCUMENT",
          clientName: clientName
      });
  }
  