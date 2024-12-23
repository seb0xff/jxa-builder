-- Droplet that allows to convert a single png file to a .icns
-- To build run: osacompile -o png2icns.app png2icns.applescript

-- created by: https://gist.github.com/Benitoite
-- fine tuned by: https://github.com/paulrudy
-- origin: https://gist.github.com/jamieweavis/b4c394607641e1280d447deed5fc85fc?permalink_comment_id=4698653#gistcomment-4698653
on open the_files
	repeat with i from 1 to the count of the_files
		tell application "Finder"
			set myFileName to POSIX path of item i of the_files
			set orig_path to POSIX path of (container of (item i of the_files) as alias)
			set exten to name extension of item i of the_files
		end tell
		set my_path to orig_path & "icon.iconset"
		do shell script "mkdir -p " & quoted form of my_path
		do shell script "sips -z 1024 1024 " & myFileName & " -s format png --out " & my_path & "/icon_512x512@2x.png"
		do shell script "sips -z 512 512 " & my_path & "/icon_512x512@2x.png --out " & my_path & "/icon_512x512.png"
		do shell script "cp " & my_path & "/icon_512x512.png " & my_path & "/icon_256x256@2x.png"
		do shell script "sips -z 256 256 " & my_path & "/icon_512x512.png --out " & my_path & "/icon_256x256.png"
		do shell script "cp " & my_path & "/icon_256x256.png " & my_path & "/icon_128x128@2x.png"
		do shell script "sips -z 128 128 " & my_path & "/icon_256x256.png --out " & my_path & "/icon_128x128.png"
		do shell script "sips -z 64 64 " & my_path & "/icon_128x128.png --out " & my_path & "/icon_32x32@2x.png"
		do shell script "sips -z 32 32 " & my_path & "/icon_32x32@2x.png --out " & my_path & "/icon_32x32.png"
		do shell script "cp " & my_path & "/icon_32x32.png " & my_path & "/icon_16x16@2x.png"
		do shell script "sips -z 16 16 " & my_path & "/icon_32x32.png --out " & my_path & "/icon_16x16.png"
		do shell script "iconutil -c icns " & my_path
		do shell script "mv " & orig_path & "/icon.icns " & orig_path & "/$(basename " & myFileName & " ." & exten & ").icns"
		do shell script "rm -r " & my_path
	end repeat
end open