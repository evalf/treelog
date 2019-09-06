import sys, os, re, fnmatch, argparse, urllib.request, functools, hashlib, subprocess


def fetch():
  parser = argparse.ArgumentParser()
  parser.add_argument('uri')
  parser.add_argument('pattern', nargs='?', default='*')
  parser.add_argument('-0', '--numberfirst', action='store_true', help='add -0 suffix to first item in sequence')
  args = parser.parse_args()

  copy = []
  overview = []
  hashes = _anchors(args.uri)
  for filename in fnmatch.filter(hashes, args.pattern):
    count = [0, 0] # present, new
    for i, hash in enumerate(hashes[filename]):
      dst = '-{}'.format(i).join(os.path.splitext(filename)) if i or args.numberfirst else filename
      new = not os.path.exists(dst)
      if new:
        copy.append((hash, dst))
      elif hash != _sha1(dst):
        sys.exit('error: file exists: {}'.format(dst))
      count[new] += 1
    overview.append('- {}: {}'.format(filename, ', '.join(['{} present', '{} new'][i].format(n) for i, n in enumerate(count) if n)))
  if not overview:
    sys.exit('no matching files.')

  print('matched {} file names:'.format(len(overview)))
  print('\n'.join(sorted(overview)))
  for hash, dst in _iterbar('copying', copy):
    print(hash, '->', dst)
    src = os.path.join(os.path.dirname(args.uri), hash + os.path.splitext(dst)[1])
    with _open(src) as fin, open(dst, 'wb') as fout:
      fout.write(fin.read())
  print('done.')


def animate():
  parser = argparse.ArgumentParser()
  parser.add_argument('uri')
  parser.add_argument('filename')
  parser.add_argument('--fps', type=int, default=25)
  parser.add_argument('--nframes', type=int, default=None)
  args = parser.parse_args()

  vcodec = {'.png': 'png', '.jpg': 'mjpeg', '.jpeg': 'mjpeg'}
  name, ext = os.path.splitext(args.filename)
  if ext.lower() not in vcodec:
    sys.exit('unsupported image format; only {} are supported'.format('/'.join(vcodec)))

  dst = name + '.mp4'
  if os.path.exists(dst) and not _confirm('destination {} exists; overwrite?'.format(dst)):
    sys.exit('aborted.')

  hashes = _anchors(args.uri)
  if args.filename not in hashes:
    sys.exit('no matching files.')

  cmd = '''ffmpeg
    -y -f image2pipe -vcodec {vcodec} -r {fps} -i -
    -movflags +faststart -r {fps}
    -c:v libx264 -preset slow -profile:v high -vf format=yuv420p -crf 16
    -bf 2 -g 30 -coder 1 {dst}
  '''.format(vcodec=vcodec[ext.lower()], fps=args.fps, dst=dst)

  p = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE)
  for hash in _iterbar('frame', hashes[args.filename][:args.nframes]):
    p.stdin.write(_read(os.path.join(os.path.dirname(args.uri), hash + ext)))

  print('waiting for encoding to finish')
  p.stdin.close()
  p.wait()
  print('finished {}'.format(dst))


def gc():
  parser = argparse.ArgumentParser()
  parser.add_argument('-y', '--yes', action='store_true', help='answer yes to all questions')
  args = parser.parse_args()

  listdir = os.listdir(os.curdir)
  pattern = re.compile(r'\b[0-9a-f]{40}[.].+?\b')
  refs = {hash for item in listdir if item.endswith('.html') for hash in pattern.findall(_read(item))}
  garbage = [item for item in listdir if pattern.match(item) and item not in refs]
  _print2(garbage)
  if garbage and not _confirm('remove {} unreferenced items?'.format(len(garbage)), auto=args.yes):
    sys.exit('aborted.')
  for item in garbage:
    os.unlink(item)
  print('no unreferenced items.')


# HELPER FUNCTIONS

def _open(uri):
  try:
    return urllib.request.urlopen(uri) if '://' in uri else open(uri, mode='rb')
  except Exception as e:
    sys.exit('error: {}'.format(e))

def _read(name):
  print('reading', name)
  with _open(name) as f:
    return f.read()

def _sha1(path, bufsize=0x20000):
  with open(path, 'rb') as f:
    h = hashlib.sha1()
    chunk = f.read(bufsize)
    while chunk:
      h.update(chunk)
      chunk = f.read(bufsize)
    return h.hexdigest()

def _anchors(uri):
  byname = {}
  for hash, ext, filename in re.findall(r'<a href="([0-9a-f]{40})([.][^"]+)" download="([^"]+\2)">\3</a>', _read(uri).decode()):
    byname.setdefault(filename, []).append(hash)
  return byname

def _print2(items):
  n, k = divmod(len(items), 2)
  L = max(map(len, items[:n+k]))
  for i in range(n):
    print(items[i].ljust(L+1), items[i-n])
  if k:
    print(items[n])

def _confirm(question, auto=False):
  if auto:
    print(question, 'yes')
    return True
  return input(question + ' yes/[no] ') == 'yes'

def _iterbar(name, iterable):
  n = len(iterable)
  if not n:
    return
  try:
    import bottombar
  except ImportError:
    yield from iterable
  else:
    m = len(name) + len(str(n)) + 10
    bar = lambda i, width: '{} {}/{} {}>'.format(name, i, n, '-' * int((i/n)*(width-m))).ljust(width-5) + ' {}%'.format((100*i)//n)
    with bottombar.BottomBar(0, format=bar) as setprogress:
      for i, item in enumerate(iterable, start=1):
        setprogress(i)
        yield item
