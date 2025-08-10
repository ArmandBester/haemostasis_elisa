# Haemostasis ELISA calculator

## Installation

* Clone the repo. Alternatively you can also download the ZIP file if you don't have git.

```
git clone https://github.com/ArmandBester/poepsnuifer.git
```
  
* cd into the cloned repo

* Build the docker image

```
docker build -t elisa_calc .
```

If using Apple ARM silicon (M1 or M2 ...) please explicitly specify the architecture using the `--platform` option as shown below. Also make sure you have a reasonably recent Rosetta installation: [https://support.apple.com/en-za/102527](https://support.apple.com/en-za/102527)

[https://docs.docker.com/get-started/](https://docs.docker.com/get-started/)

```
docker build -t elisa_calc .  --platform linux/amd64
```

* Run the image
  
```
docker run -p 8501:8501 elisa_calc
```

You should now see something like this in the command line:

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501

```

If using this on your own machine you can go to the `localhost` link or if you want to have this on a dedicated machine in your organization you can follow the IP address of the machine 'xxx.xxx.xxx.xxx:8501'
