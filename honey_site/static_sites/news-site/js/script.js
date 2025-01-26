import { additionalCreep } from './creep.min.js';
var mus = new Mus();
var cookieName = "etriganId";
var fingerprintCookieName = "etriganFingerprint";
var visitorId = null;
var keyboardEvents = [];
var mouseEventsLimit = 7;
var keyboardEventsLimit = 7;

function sendData(d, endpoint) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.withCredentials = true;
    xmlhttp.open("POST", endpoint);
    xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xmlhttp.send(JSON.stringify(d))
}

function recordMouseEvents() {
    mus.record();
    setInterval(function() {
	var data = mus.getData();
	if (data.frames.length > mouseEventsLimit) {
	    var mouseMovementObject = {};
	    mouseMovementObject.visitorId = visitorId;
	    mouseMovementObject.sourcePage = window.location.href;
	    mouseMovementObject.mouseMovements = data.frames;
	    sendData(mouseMovementObject, "/mm");
	    mus.release();
	    mus.record();
	}
    }, 500);
}

function getCookie(name) {
    var match = document.cookie.match(RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
    return match ? match[1] : null;
}

document.onkeydown = function(e) {
    if (!visitorId)
	return;
    
    keyboardEvents.push(e.key);
    
    if (keyboardEvents.length >= keyboardEventsLimit) {
	var keyboardObject = {}
	keyboardObject.visitorId = visitorId;
	keyboardObject.sourcePage = window.location.href;
	keyboardObject.keyboardEvents = keyboardEvents;
	sendData(keyboardObject, "/mm");
	keyboardEvents = [];
    }
}


if (!getCookie(cookieName)) {
    var now = new Date();
    var time = now.getTime();
    var expireTime = time + 3000000 * 3600;
    now.setTime(expireTime);
    
    document.cookie = cookieName + "=" + Math.floor(Math.random() * 1000000000) +
	";expires=" + now.toUTCString() + ";path=/";
    
}

const fpPromise = import('./flib.js')
      .then(FingerprintJS => FingerprintJS.load())

fpPromise
    .then(fp => fp.get())
    .then(result => {
	
	const botdPromise = import('./botdlib.js')
	      .then((Botd) => Botd.load())
	
	botdPromise
	    .then(botd => botd.detect())
	    .then(botdRes => {
		additionalCreep().then(addedFP => {
		    var now = new Date();
		    var time = now.getTime();
		    var expireTime = time + 3000000 * 3600;
		    now.setTime(expireTime);
		    document.cookie = fingerprintCookieName + "=" + result.visitorId +
			";expires=" + now.toUTCString() + ";path=/";
		    var fpObject = {}
		    fpObject.sourcePage = window.location.href
		    fpObject.result = JSON.stringify(result)
		    fpObject.addedFP = JSON.stringify(addedFP)
		    fpObject.botResult = botdRes
		    sendData(fpObject, "/fp")
		    visitorId = result.visitorId
		})
	})
})

window.onload = function() {
    recordMouseEvents()
}
