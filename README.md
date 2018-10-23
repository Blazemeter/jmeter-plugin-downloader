####How to run:

1. Install docker
2. Clone repo
3. Run `docker build -t jpd`
4. Run `docker run -v /tmp/jpd:/tmp/jpd jpd <cli args>`
5. Get results from `/tmp/jpd/out.zip`

##### Cli Args:
```
Usage: main.py [OPTIONS]

Options:
  --source-url TEXT       JMeter plugin source URL. Default: https://jmeter-
                          plugins.org/repo/
  --dest-url TEXT         JMeter plugin destination URL.  [required]
  --jmeter-versions TEXT  JMeter versions to support. Default: 5.0,4.0,3.3
  --dry-run               Should create index.json only and zip it.
  --help                  Show this message and exit.
```