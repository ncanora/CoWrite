<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ncanora/CoWrite">
    <img src="icon.png" alt="CoWrite Logo" width="200" height="200">
  </a>

  <h1 align="center">CoWrite Collaborative Text Editor</h1>

  <p align="center">
    A real-time collaborative text editor built with Go and QuillJS.
    <br />
    <a href="https://github.com/ncanora/CoWrite"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/ncanora/CoWrite">View Demo</a>
    ·
    <a href="https://github.com/ncanora/CoWrite/issues">Report Bug</a>
    ·
    <a href="https://github.com/ncanora/CoWrite/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#setup">Setup</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
<br>
![CoWrite Screenshot](images/screenshot.png)

**CoWrite** is a real-time collaborative text editor that allows multiple users to edit documents simultaneously.


### Built With

**Backend:**
- [Go](https://golang.org/) - Programming Language
- [Gorilla WebSockets](https://github.com/gorilla/websocket) - WebSocket Implementation for Go

**Frontend:**
- [QuillJS](https://quilljs.com/) - Rich Text Editor
- [Quill-Cursors](https://github.com/reedsy/quill-cursors) - Collaborative Cursors Module for QuillJS


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- INSTALLATION -->
## Installation
<br>
Follow these steps to set up the project locally for development and testing purposes.

### Prerequisites

Ensure you have the following installed on your machine:

- **Go:** [Download and install Go](https://golang.org/doc/install)
- **Node.js & NPM:** [Download and install Node.js](https://nodejs.org/en/download/)
- **Git:** [Download and install Git](https://git-scm.com/downloads)

### Setup

1. **Clone the Repository**
    ```sh
    git clone https://github.com/ncanora/CoWrite.git
    ```
    
2. **Start the Go Server/Host Process**
    ```sh
    go run *.go
    ```
    
    This will start create a document called test.txt (if one has not already been created) for clients to edit.
   
3. Connect to the host/server in a browser `http://IP:PORTNO`
   
4. Enter a nickname that will be shown to other clients, you can enter anything for the key (not implemented yet)
   
5. You should now be editing your CoWrite document! You should be able to see when new clients connect, see their edits in realtime, and see which cursor is who's by hovering your mouse over another client's cursor.
