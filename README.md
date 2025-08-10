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

---

## About the curve fitting

### Four Parameter Logistig equation (4PL)

$$
y = d + \frac{a - d}{1 + \left(\frac{x}{c}\right)^b}
$$

[Source](https://www.myassays.com/four-parameter-logistic-regression.html)

Of course x = the independent variable and y = the dependent variable just as in the linear model above. The 4 estimated parameters consist of the following:

* a = the minimum value that can be obtained (i.e. what happens at 0 dose)

* d = the maximum value that can be obtained (i.e. what happens at infinite dose)

* c = the point of inflection (i.e. the point on the S shaped curve halfway between a and d)

* b = Hill’s slope of the curve (i.e. this is related to the steepness of the curve at point c).

The `d` parameter here is key. Remember the Hill equation for cooperativity, haemoglobin and how cool that mechanism is.

This equation rearranges easily also, since the `x` only appears once, unlike the one-site binding.

$$
x = c\bigg(\frac{a-d}{y-d} - 1\bigg)^\frac{1}{b}
$$

### Another calculator
[Online 4PL calculator](https://www.aatbio.com/tools/four-parameter-logistic-4pl-curve-regression-online-calculator)

### NotebookML audio deep dive


https://github.com/user-attachments/assets/6e0e7fd8-5df2-481a-a826-7ae4bb02044c







