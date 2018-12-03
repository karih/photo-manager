# Runs development server

from .. import app

def main(*args):
    app.run(port=8000)

if __name__ == '__main__':
    main()
