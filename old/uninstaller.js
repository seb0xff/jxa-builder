ObjC.import("Foundation");

var fileManager = $.NSFileManager.defaultManager;

var sourceFolderPath =
  "/Users/sebastian/Documents/src/js/DoubleClickConsoleEdit/build/output";
// var destinationFolderPath = "/Users/sebastian/Library/Script Libraries";
var destinationFolderPath = "/Library/Script Libraries";

var fileList = ["jxa-path1_0_0.scpt"];

for (var i = 0; i < fileList.length; i++) {
  var currentFile = fileList[i];
  var sourcePath = sourceFolderPath + "/" + currentFile;
  var destinationPath = destinationFolderPath + "/" + currentFile;

  var sourceURL = $.NSURL.fileURLWithPath(sourcePath);
  var destinationURL = $.NSURL.fileURLWithPath(destinationPath);

  var errorPtr = Ref();
  fileManager.copyItemAtURLToURLError(sourceURL, destinationURL, errorPtr);

  if (errorPtr.value) {
    console.log("Error: " + errorPtr.value);
  } else {
    console.log("File copied: " + currentFile);
  }
}
