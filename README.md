# KDM-validator

This program allows you to validate the Key Delivery Message (KDM) received from your distributor.

Your might accidentally receive a KDM for a wrong server or with an incorrect validity period. 

The validator checks if:
 1. your server ID is present in the KDM file
 2. the validity period includes your movie's time window
 3. the KDM's content title matches the movie

You need to configure three parameters
```
KDM_FOLDER --> Path where KDM files are downloaded
JSON_URL   --> JSON endpoint
SERIAL     --> ID of your sever (6 digits string)
```

![Screenshot](img/screen.png?raw=true "Screenshot")

## JSON endpoint
The configured URL should provide a list of movies with their title and the timestamps of the first and last show in the following JSON format

```json
[{
	"title": "Pete's Dragon",
	"min_TS": "1473519600",
	"max_TS": "1473604200"
}, {
	"title": "Ice Age: Collision Course",
	"min_TS": "1474124400",
	"max_TS": "1474295400"
}, {
	"title": "Finding Dory",
	"min_TS": "1475262000",
	"max_TS": "1475418600"
}]
```

```sh
$ python kdm_validator.py
```

### Release Notes:
  - This program requires Python with Tkinter module
