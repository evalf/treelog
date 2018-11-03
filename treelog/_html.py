# Copyright (c) 2018 Evalf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import contextlib, sys, os, urllib.parse, html, hashlib
from . import _base, _io

class HtmlLog(_base.Log):
  '''Output html nested lists.'''

  def __init__(self, dirpath, *, filename='log.html', title=None, htmltitle=None, favicon=None):
    self._dir = _io.directory(dirpath)
    for self.filename in _io.sequence(filename):
      self._file = self._dir.open(self.filename, 'w')
      if self._file:
        break
    css = hashlib.sha1(CSS.encode()).hexdigest() + '.css'
    with self._dir.open(css, 'w') as f:
      f.write(CSS)
    js = hashlib.sha1(JS.encode()).hexdigest() + '.js'
    with self._dir.open(js, 'w') as f:
      f.write(JS)
    if title is None:
      title = ' '.join(sys.argv)
    if htmltitle is None:
      htmltitle = html.escape(title)
    if favicon is None:
      favicon = FAVICON
    self._file.write(HTMLHEAD.format(title=title, htmltitle=htmltitle, css=css, js=js, favicon=favicon))
    self._html_depth = 0 # number of currently open html elements nested under the "log" div
    self._context = []

  def pushcontext(self, title):
    self._context.append(title)

  def popcontext(self):
    if self._html_depth == len(self._context):
      print('</div><div class="end"></div></div>', file=self._file)
      self._html_depth -= 1
    self._context.pop()

  def write(self, text, level, escape=True):
    for c in self._context[self._html_depth:]:
      print('<div class="context"><div class="title">{}</div><div class="children">'.format(html.escape(c)), file=self._file)
    self._html_depth = len(self._context)
    if escape:
      text = html.escape(text)
    print('<div class="item" data-loglevel="{}">{}</div>'.format(level, text), file=self._file, flush=True)

  @contextlib.contextmanager
  def open(self, filename, mode, level, id):
    base, ext = os.path.splitext(filename)
    try:
      f = None
      if id:
        fname = id.hex() + ext
        f = self._dir.open(fname, mode, name=filename)
      else:
        f, fname = self._dir.temp(mode, name=filename)
      with self.context(filename), f:
        yield f
    except:
      if f:
        self._dir.unlink(fname)
      raise
    if id:
      realname = fname
    else:
      realname = self._dir.hash(fname, 'sha1').hex() + ext
      self._dir.link(fname, realname)
      self._dir.unlink(fname)
    self.write('<a href="{href}">{name}</a>'.format(href=urllib.parse.quote(realname), name=html.escape(filename)), level, escape=False)

  def close(self):
    if hasattr(self, '_file') and not self._file.closed:
      self._file.write(HTMLFOOT)
      self._file.close()
      return True

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self.close()

  def __del__(self):
    if self.close():
      warnings.warn('unclosed object {!r}'.format(self), ResourceWarning)

HTMLHEAD = '''\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, minimum-scale=1, user-scalable=no"/>
<title>{title}</title>
<script src="{js}"></script>
<link rel="stylesheet" type="text/css" href="{css}"/>
<link rel="icon" href="{favicon}"/>
</head>
<body>
<div id="header"><div id="bar"><div id="text"><div id="title">{htmltitle}</div></div></div></div>
<div id="log">
'''

HTMLFOOT = '''\
</div></body></html>
'''

CSS = '''\
body { font-family: monospace; font-size: 12px; }

a, a:visited, a:hover { color: inherit; text-decoration: underline; }

.button { cursor: pointer; -webkit-tap-highlight-color: transparent; user-select: none; -moz-user-select: none; -webkit-user-select: none; }

#header { position: fixed; top: 0px; left: 0px; right: 0px; z-index: 2; }
#bar { height: 48px; display: flex; width: 100%; padding: 0px 4px; box-sizing: border-box; align-items: center; }
#log, #theater { position: fixed; top: 48px; left: 0px; right: 0px; bottom: 0px; width: 100%; height: calc(100% - 48px); }
#log { overflow: auto; padding: 10px; box-sizing: border-box; }

#header { box-shadow: 0px 0px 4px 2px hsla(0,0%,0%,0.25); }
#bar { color: #fff; background: hsl(205,46%,45%); }
#header > .dropdown { background: hsla(205,46%,90%,0.9); border-bottom: 2px solid hsl(205,46%,45%); color: #000; }
body[data-show='theater'] #bar { background: hsl(140,46%,45%); }
body[data-show='theater'] #header > .dropdown { background: hsla(140,46%,90%,0.9); border-bottom: 2px solid hsl(140,46%,45%); }
#bar, #header > .dropdown { transition: background .25s, border-bottom-color .25s; }

#bar > *, #text > * { margin: 0px 4px; }
#text { display: flex; flex-direction: row; align-items: center; flex: 1 1 auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#text :first-child { margin-left: 0px; }
#text :last-child { margin-right: 0px; }
#title { font-weight: bold; }

#bar svg { stroke: #fffb; fill: #fffb; }
#bar .icon { flex: 0 0 auto; width: 32px; height: 32px; border-radius: 2px; }
#bar .small-icon-container { display: grid; align-items: center; justify-items: center; }
#bar .icon.button { transition: background .25s; }
#bar .icon.button:hover { background: #fff4; }

body[data-show='theater'] .show-if-log,
body:not([data-show='theater']) .show-if-theater,
body.theater-locked .show-if-theater-unlocked,
body:not(.theater-locked) .show-if-theater-locked,
body.droppeddown .hide-if-droppeddown,
body:not(.droppeddown) .show-if-droppeddown { display: none !important; }

#bar > .hamburger { display: grid; grid-template-rows: 2px 2px 2px; grid-template-columns: 18px; grid-gap: 3px; align-content: center; justify-content: center; }
#bar > .hamburger > * { background: #fffb; border-radius: 1px; }
body.droppeddown #bar > .hamburger { background: #fff4; }

.dropdown-catchall { display: none; }
body.droppeddown .dropdown-catchall { display: block; position: fixed; top: 0px; left: 0px; right: 0px; bottom: 0px; background: #0004; z-index: 1; }

#header > .dropdown { display: none; max-height: 60%; overflow: auto; }
body.droppeddown #header > .dropdown { display: block; padding: 20px 10px; }
#header > .dropdown .key_description { display: grid; grid-template-columns: max-content 1fr; align-items: center; grid-gap: 5px 10px; }
#header > .dropdown .key_description .keys { display: inline-grid; justify-self: right; cursor: pointer; font-family: monospace; user-select: none; -moz-user-select: none; -webkit-user-select: none; border: 1px solid black; border-radius: 2px; height: 32px; align-items: center; padding: 0px 10px; }

#log .item, #log .context > .title { white-space: pre; padding-top: 5px; }

#log .item[data-loglevel='0'] { color: gray; }
#log .item[data-loglevel='1'] { color: black; }
#log .item[data-loglevel='2'] { color: blue; }
#log .item[data-loglevel='3'] { color: orange; }
#log .item[data-loglevel='4'] { color: red; }

#log .context > * { display: inline-block; vertical-align: top; }
#log .context > .title { color: gray; cursor: pointer; }
#log .context > .children { margin-left: 10px; border-left: 1px solid #ddd; padding-left: 10px; margin-bottom: 5px; }
#log .context.collapsed > .title::after { content: ' (collapsed)'; font-style: italic; }
#log .context.collapsed > .children { display: none; }
#log .context > .end { display: none; }

#log a.plot { text-decoration-color: #ddd; }

#log .post-mortem { white-space: pre; }

body.hide0 #log [data-loglevel='0'],
body.hide1 #log [data-loglevel='1'],
body.hide2 #log [data-loglevel='2'],
body.hide3 #log [data-loglevel='3'],
body.hide4 #log [data-loglevel='4'] { display: none; }


#theater { overflow: hidden; touch-action: none; background: white; box-sizing: border-box; }
#theater.overview { display: grid; background: #eee; padding: 20px; grid-gap: 20px; align-items: center; justify-items: center; }
body:not([data-show='theater']) #theater { display: none; }

#theater:not(.overview) img.plot { object-fit: contain; width: 100%; height: 100%; }
#theater.overview img.plot.selected { border: 2px solid #888; margin: -2px; }
body.theater-locked #theater.overview img.plot.selected_category:not(.selected) { border: 2px solid #ddd; margin: -2px; }
#theater.overview .plot_container1 { position: relative; width: 100%; height: 100%; }
#theater.overview .plot_container2 { position: absolute; width: 100%; height: 100%; top: 0px; left: 0px; right: 0px; bottom: 0px; }
#theater.overview .plot_container3 { height: calc(100% - 20px); display: flex; align-items: center; justify-content: center; }
#theater.overview .plot { background: white; max-width: 100%; max-height: 100%; }
#theater.overview .label { position: absolute; width: 100%; left: 0px; right: 0px; bottom: 0px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
'''

JS = '''\
'use strict';

// LOW LEVEL UTILS

const create_element = function(tag, options, ...children) {
  const el = document.createElement(tag);
  options = options || {};
  for (const k in options)
    if (k === 'events')
      for (name in options[k])
        el.addEventListener(name, options[k][name]);
    else if (k === 'dataset')
      for (name in options[k])
        el.dataset[name] = options[k][name];
    else
      el.setAttribute(k, options[k]);
  for (const child of children)
    el.appendChild(typeof(child) === 'string' ? document.createTextNode(child) : child);
  return el;
};

const create_svg_element = function(tag, options, ...children) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  options = options || {};
  for (const k in options)
    if (k === 'events')
      for (name in options[k])
        el.addEventListener(name, options[k][name]);
    else
      el.setAttribute(k, options[k]);
  for (const child of children)
    el.appendChild(child);
  return el;
};

const union_dict = function(...elements) {
  if (elements.length == 1)
    return elements[0];
  const union = {};
  for (const elem of elements)
    Object.assign(union, elem);
  return union;
};

// ART

const create_lock = function(options) {
  const hw = 6;  // half width
  const hh = 5;  // half height
  const so = 5;  // inner radius of the shackle
  const si = 4;  // outer radius of the shackle
  const sh = 2;  // length of the straight part of the shackle
  const su = 5;  // length of the straight part of the shackle unlocked
  return (
    create_svg_element('svg', union_dict({viewBox: '-16 -18 32 32'}, options),
      create_svg_element('path', {'class': 'show-if-theater-locked', stroke: 'none', d: `M ${-hw},${-hh} v ${2*hh} h ${2*hw} v ${-2*hh} h ${so-hw} v ${-sh} a ${so} ${so} 0 0 0 ${-2*so} 0 v ${sh} Z M ${-si} ${-hh} v ${-sh} a ${si} ${si} 0 0 1 ${2*si} 0 v ${sh} Z`}),
      create_svg_element('path', {'class': 'show-if-theater-unlocked', stroke: 'none', d: `M ${-hw},${-hh} v ${2*hh} h ${2*hw} v ${-2*hh} h ${so-hw} v ${-su} a ${si} ${si} 0 0 1 ${2*si} 0 v ${su} h ${so-si} v ${-su} a ${so} ${so} 0 0 0 ${-2*so} 0 v ${su} Z`})));
};

const log_level_paths = {
  0: 'M -4 -4 L 2 -4 L 4 -2 L 4 2 L 2 4 L -4 4 Z',
  1: 'M -2 -4 L 2 -4 M 0 -4 L 0 4 M -2 4 L 2 4',
  2: 'M -4 -4 L -4 4 L 4 4 L 4 -4',
  3: 'M -4 -4 L -4 4 L 4 4 L 4 -4 M 0 4 L 0 -1',
  4: 'M 4 -4 L -4 -4 L -4 4 L 4 4 M -4 0 L 1 0'
};

const create_log_level_icon = function(level, options) {
  return (
    create_svg_element('svg', union_dict({viewBox: '-9 -9 18 18', style: 'width: 18px; height: 18px; border-radius: 1px;'}, options),
      create_svg_element('mask', {id: 'm'},
        create_svg_element('path', {d: 'M -10 -10 L -10 10 L 10 10 L 10 -10 Z', fill: 'white', stroke: 'none'}),
        create_svg_element('path', {d: log_level_paths[level], fill: 'none', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', stroke: 'black'})),
      create_svg_element('path', {mask: 'url(#m)', d: 'M -9 -9 L -9 9 L 9 9 L 9 -9 Z', stroke: 'none'})));
};

// LOG

// NOTE: This should match the log levels defined in the `treelog` module.
const LEVELS = ['debug', 'info', 'user', 'warning', 'error'];
const VIEWABLE = ['.jpg', '.jpeg', '.png', '.svg'];
// Make sure `VIEWABLE.filter(suffix => filename.endsWith(suffix))[0]` is always the longest match.
VIEWABLE.sort((a, b) => b.length - a.length);

const Log = class {
  constructor() {
    this.root = document.getElementById('log');
  }
  get state() {
    return {collapsed: this.collapsed, loglevel: this.loglevel};
  }
  set state(state) {
    // We deliberately ignore state changes, except during reloads (handled by
    // `init_elements` and `set loglevel` in the `window`s load event handler,
    // respectively).
  }
  get collapsed() {
    const collapsed = {};
    for (const context of document.querySelectorAll('#log .context.collapsed'))
      collapsed[context.dataset.id] = true;
    return collapsed;
  }
  get loglevel() {
    return parseInt(document.body.dataset.loglevel || 2);
  }
  set loglevel(level) {
    level = Math.max(0, Math.min(LEVELS.length-1, level));
    for (let i = 0; i < LEVELS.length; i++)
      document.body.classList.toggle('hide'+i, i < level);
    document.body.dataset.loglevel = level;
    const indicator = document.getElementById('log-level-indicator');
    if (indicator) {
      indicator.innerHTML = '';
      indicator.appendChild(create_log_level_icon(level));
    }
    if (this.state.loglevel !== level) {
      this.state.loglevel = level;
      update_state();
    }
  }
  keydown(ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey)
      return false;
    else if (ev.key.toLowerCase() == 'c') { // Collapse all.
      for (const context of document.querySelectorAll('#log .context'))
        if (context.lastElementChild && context.lastElementChild.classList.contains('end'))
          context.classList.add('collapsed');
      update_state();
    }
    else if (ev.key.toLowerCase() == 'e') { // Expand all.
      for (const context of document.querySelectorAll('#log .context'))
        context.classList.remove('collapsed');
      update_state();
    }
    else if (ev.key == '+' || ev.key == '=') { // Increase loglevel.
      this.loglevel = this.loglevel+1;
      update_state();
    }
    else if (ev.key == '-') { // Decrease loglevel.
      this.loglevel = this.loglevel-1;
      update_state();
    }
    else
      return false;
    return true;
  }
  *_reverse_contexts_iterator(context) {
    while (true) {
      if (!context || !context.classList.contains('context'))
        return;
      yield context;
      context = context.parentElement;
      if (!context)
        return;
      context = context.parentElement;
    }
  }
  init_elements(collapsed) {
    // Assign unique ids to context elements, collapse contexts according to
    // `state`.
    {
      let icontext = 0;
      for (const context of document.querySelectorAll('#log .context')) {
        context.dataset.id = icontext;
        context.classList.toggle('collapsed', collapsed[icontext] || false);
        icontext += 1;
        let label = [];
        for (let part of this._reverse_contexts_iterator(context))
          label.unshift((part.querySelector(':scope > .title') || {innerText: '?'}).innerText);
        context.dataset.label = label.join('/');
      }
    }

    // Assign (highest) log levels of children to context: loop over all items
    // and assign the item log level to parent context elements until the context
    // not has a higher level.
    for (const item of document.querySelectorAll('#log .item')) {
      const loglevel = parseInt(item.dataset.loglevel);
      let parent = item.parentElement;
      if (parent)
        parent = parent.parentElement;
      // NOTE: `parseInt` returns `NaN` if the `parent` loglevel is undefined and
      // `NaN < loglevel` is false.
      while (parent && parent.classList.contains('context') && !(parseInt(parent.dataset.loglevel) >= loglevel)) {
        parent.dataset.loglevel = loglevel;
        parent = parent.parentElement;
        if (parent)
          parent = parent.parentElement;
      }
    }

    // Link viewable anchors to theater.
    let ianchor = 0;
    for (const anchor of document.querySelectorAll('#log .item > a')) {
      const filename = anchor.innerText;
      const suffix = VIEWABLE.filter(suffix => filename.endsWith(suffix));
      if (!suffix.length)
        continue;
      const stem = filename.slice(0, filename.length - suffix[0].length);
      if (!stem)
        continue;
      const category = (stem.match(/^(.*?)[0-9]*$/) || [null, null])[1];
      anchor.addEventListener('click', this._plot_clicked);

      let context = null;
      let parent = anchor.parentElement;
      if (parent)
        parent = parent.parentElement;
      if (parent)
        parent = parent.parentElement;
      if (parent && parent.classList.contains('context'))
        context = parent;
      else
        context = {dataset: {}};

      anchor.id = `plot-${ianchor}`;
      ianchor += 1;
      theater.add_plot(anchor.href, anchor.id, category, context.dataset.id, (context.dataset.label ? context.dataset.label + '/' : '') + stem);
    }

    // Make contexts clickable.
    for (const title of document.querySelectorAll('#log .context > .title'))
      title.addEventListener('click', this._context_toggle_collapsed);
  }
  _plot_clicked(ev) {
    ev.stopPropagation();
    ev.preventDefault();
    window.history.pushState(window.history.state, 'log');
    theater.href = ev.currentTarget.href;
    document.body.dataset.show = 'theater';
    update_state();
  }
  _context_toggle_collapsed(ev) {
    // `ev.currentTarget` is the context title element (see https://developer.mozilla.org/en-US/docs/Web/API/Event/currentTarget)
    const context = ev.currentTarget.parentElement;
    context.classList.toggle('collapsed');
    update_state();
    ev.stopPropagation();
    ev.preventDefault();
  }
  scroll_into_view(anchor_id) {
    const anchor = document.getElementById(anchor_id);
    if (anchor) {
      let parent = anchor.parentElement;
      while (parent && parent.id != 'log') {
        if (parent.classList.contains('context'))
          parent.classList.remove('collapsed');
        parent = parent.parentElement;
      }
      anchor.scrollIntoView();
      update_state();
    }
  }
};

// THEATER

const Theater = class {
  constructor() {
    this.root = create_element('div', {id: 'theater', events: {'pointerdown': this.pointerdown.bind(this), 'pointerup': this.pointerup.bind(this)}});

    this.plots_per_category = {undefined: []};
    this.plots_per_context = {};
    this.info = {};
    this.touch_scroll_delta = 25;
  }
  add_plot(href, anchor_id, category, context, label) {
    const info = {href: href, anchor_id: anchor_id, category: category, index: this.plots_per_category[undefined].length, context: context, label: label};
    this.plots_per_category[undefined].push(href);
    if (category) {
      if (!this.plots_per_category[category])
        this.plots_per_category[category] = [];
      info.index_category = this.plots_per_category[category].length;
      this.plots_per_category[category].push(href);
    }
    if (!this.plots_per_context[context])
      this.plots_per_context[context] = [];
    this.plots_per_context[context].push(href);
    this.info[href] = info;
  }
  get locked() {
    return document.body.classList.contains('theater-locked');
  }
  set locked(locked) {
    if (locked === undefined)
      return;
    locked = Boolean(locked);
    if (this.locked == locked)
      return;
    document.body.classList.toggle('theater-locked', locked);
    update_state();
  }
  toggle_locked() {
    document.body.classList.toggle('theater-locked');
  }
  get overview() {
    return this.root.classList.contains('overview');
  }
  set overview(overview) {
    if (overview === undefined)
      return;
    overview = Boolean(overview);
    if (this.root.classList.contains('overview') == overview)
      return;
    if (overview)
      this._draw_overview();
    else
      this._draw_plot();
    this._update_selection();
    update_state();
  }
  toggle_overview() { this.overview = !this.overview; }
  get category() {
    return this.href ? this.info[this.href].category : undefined;
  }
  get index() {
    return this.href && (this.locked ? this.info[this.href].index_category : this.info[this.href].index);
  }
  get href() {
    return this._href;
  }
  set href(href) {
    if (href === undefined || this._href == href)
      return;
    const old_href = this._href;
    this._href = href;
    if (this.overview) {
      const old_context = old_href && this.info[old_href].context;
      const new_context = this.info[this._href].context;
      if (old_context != new_context)
        this._draw_overview();
    } else
      this._draw_plot();
    this._update_selection();
    document.getElementById('theater-label').innerText = this.info[this._href].label;
    update_state();
  }
  _draw_plot() {
    const plot = create_element('img', {src: this.href, 'class': 'plot', dataset: {category: this.info[this.href].category || ''}, events: {click: this._blur_plot.bind(this)}});
    this.root.innerHTML = '';
    this.root.classList.remove('overview');
    this.root.appendChild(plot);
  }
  _draw_overview() {
    this.root.innerHTML = '';
    this.root.classList.add('overview');
    this._update_overview_layout();
    for (const href of this.plots_per_context[this.info[this.href].context]) {
      const plot = create_element('img', {src: href, 'class': 'plot', dataset: {category: this.info[href].category || ''}, events: {click: this._focus_plot.bind(this)}});
      const plot_container3 = create_element('div', {'class': 'plot_container3'}, plot);
      const plot_container2 = create_element('div', {'class': 'plot_container2'}, plot_container3);
      if (this.info[href].category)
        plot_container2.appendChild(create_element('div', {'class': 'label'}, this.info[href].category));
      this.root.appendChild(create_element('div', {'class': 'plot_container1'}, plot_container2));
    }
  }
  _update_selection() {
    const category = this.category;
    for (const plot of this.root.querySelectorAll('img.plot')) {
      plot.classList.toggle('selected', plot.src == this.href);
      plot.classList.toggle('selected_category', plot.dataset.category == category);
    }
  }
  _update_overview_layout() {
    let nplots;
    try {
      nplots = this.plots_per_context[this.info[this.href].context].length;
    } catch (e) {
      return;
    }
    const plot_aspect = 640 / 480;
    const screen_width = window.innerWidth;
    const screen_height = window.innerHeight;
    let optimal_nrows = 1;
    let optimal_size = 0;
    for (let nrows = 1; nrows <= nplots; nrows += 1) {
      const ncols = Math.ceil(nplots / nrows);
      const size = Math.min(screen_width*screen_width/(ncols*ncols)/plot_aspect, screen_height*screen_height/(nrows*nrows)*plot_aspect);
      if (size > optimal_size) {
        optimal_nrows = nrows;
        optimal_size = size;
      }
    }
    let optimal_ncols = Math.ceil(nplots / optimal_nrows);
    this.root.style.gridTemplateColumns = Array(optimal_ncols).fill('1fr').join(' ');
    this.root.style.gridTemplateRows = Array(optimal_nrows).fill('1fr').join(' ');
  }
  _focus_plot(ev) {
    this.href = ev.currentTarget.src;
    this.overview = false;
    ev.preventDefault();
    ev.stopPropagation();
  }
  _blur_plot(ev) {
    this.overview = true;
    ev.preventDefault();
    ev.stopPropagation();
  }
  get current_plots() {
    return this.plots_per_category[this.locked && this.category || undefined];
  }
  next() {
    this.href = this.current_plots[this.index+1];
  }
  previous() {
    this.href = this.current_plots[this.index-1];
  }
  first() {
    this.href = this.current_plots[0];
  }
  last() {
    const plots = this.current_plots;
    this.href = plots[plots.length-1];
  }
  get state() {
    return {href: this.href, locked: this.locked, overview: this.overview};
  }
  set state(state) {
    if (state === undefined)
      return;
    this.href = state.href;
    if (state.locked !== undefined)
      this.locked = state.locked;
    if (state.overview !== undefined)
      this.overview = state.overview;
  }
  _open_log() {
    document.body.dataset.show = '';
    update_state(true);
    log.scroll_into_view(this.info[this.href].anchor_id);
  }
  keydown(ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey)
      return false;
    else if (ev.key == ' ')
      this.locked = !this.locked;
    else if (ev.key == 'Tab')
      this.overview = !this.overview;
    else if (ev.key == 'ArrowLeft' || ev.key == 'PageUp' || ev.key.toLowerCase() == 'k')
      this.previous();
    else if (ev.key == 'ArrowRight' || ev.key == 'PageDown' || ev.key.toLowerCase() == 'j')
      this.next();
    else if (ev.key == 'Home' || ev.key == '^')
      this.first();
    else if (ev.key == 'End' || ev.key == '$')
      this.last();
    else if (ev.key == 'Escape')
      window.history.back();
    else if (ev.key.toLowerCase() == 'q')
      this._open_log();
    else
      return false;
    return true;
  }
  pointerdown(ev) {
    if (ev.pointerType != 'touch' || !ev.isPrimary)
      return;
    this._touch_scroll_pos = ev.screenY;
    // NOTE: This introduces a cyclic reference.
    this._pointer_move_handler = this.pointermove.bind(this);
    this.root.addEventListener('pointermove', this._pointer_move_handler);
  }
  pointermove(ev) {
    if (ev.pointerType != 'touch' || !ev.isPrimary)
      return;
    if (Math.abs(ev.screenY-this._touch_scroll_pos) > this.touch_scroll_delta) {
      if (ev.screenY < this._touch_scroll_pos - this.touch_scroll_delta) {
        const delta_index = Math.floor((this._touch_scroll_pos-ev.screenY) / this.touch_scroll_delta);
        const index = Math.max(0, this.index - delta_index);
        this._touch_scroll_pos = index == 0 ? ev.screenY : this._touch_scroll_pos - delta_index*this.touch_scroll_delta;
        this.href = this.current_plots[index];
      }
      else if (ev.screenY > this._touch_scroll_pos + this.touch_scroll_delta) {
        const delta_index = Math.floor((ev.screenY-this._touch_scroll_pos) / this.touch_scroll_delta);
        const max_index = this.current_plots.length - 1;
        const index = Math.min(max_index, this.index + delta_index);
        this._touch_scroll_pos = index == max_index ? ev.screenY : this._touch_scroll_pos + delta_index*this.touch_scroll_delta;
        this.href = this.current_plots[index];
      }
    }
  }
  pointerup(ev) {
    if (ev.pointerType != 'touch' || !ev.isPrimary)
      return;
    this._touch_scroll_pos = undefined;
    this.root.removeEventListener('pointermove', this._pointer_move_handler);
  }
};

// GLOBAL

// Disabled during initialization.  Will be enabled by the window load event
// handler.
let state_control = 'disabled';

const update_state = function(push) {
  if (state_control == 'disabled')
    return;
  let state;
  if (document.body.dataset.show == 'theater')
    state = {show: 'theater', theater: theater.state};
  else
    state = {show: '', log: log.state}
  if (push)
    window.history.pushState(state, 'log');
  else
    window.history.replaceState(state, 'log');
}

const apply_state = function(state) {
  const _state_control = state_control;
  state_control = 'disabled';
  if (state.show == 'theater')
    theater.state = state.theater;
  if (state.log)
    log.state = state.log;
  document.body.dataset.show = state.show || '';
  state_control = _state_control;
  // The collapsed state is not changed by going back or forward in the
  // history.  We do store the collapsed state in `window.history.state` to
  // preserve the collapsed state during a reload.  We call `update_state` here
  // because the restored state might have a different collapsed state.
  update_state();
}

const keydown_handler = function(ev) {
  if (ev.key == 'Escape' && document.body.classList.contains('droppeddown'))
    document.body.classList.remove('droppeddown');
  else if (document.body.dataset.show == 'theater' && theater.keydown(ev))
    ;
  else if (!document.body.dataset.show && log.keydown(ev))
    ;
  else if (ev.altKey || ev.ctrlKey || ev.metaKey)
    return;
  else if (ev.key == '?')
    document.body.classList.toggle('droppeddown');
  else if (ev.key.toLowerCase() == 'r') { // Reload.
    window.location.reload(true);
  }
  else if (ev.key.toLowerCase() == 'l') { // Load latest.
    if (document.body.dataset.latest)
      window.location.href = document.body.dataset.latest + '?' + Date.now();
  }
  else
    return;
  ev.stopPropagation();
  ev.preventDefault();
}

window.addEventListener('load', function() {
  const grid = create_element('div', {'class': 'key_description'});
  const _add_key_description = function(cls, keys, description, _key) {
    grid.appendChild(create_element('div', {'class': cls+' keys', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); window.dispatchEvent(new KeyboardEvent('keydown', {key: _key})); }}}, keys.join('+')));
    grid.appendChild(create_element('div', {'class': cls}, description));
  }
  _add_key_description('', ['R'], 'Reload.', 'R');
  _add_key_description('', ['L'], 'Load latest.', 'L');
  _add_key_description('show-if-log', ['+'], 'Increase log verbosity.','+');
  _add_key_description('show-if-log', ['-'], 'Decrease log verbosity.','-');
  _add_key_description('show-if-log', ['C'], 'Collapse all contexts.','C');
  _add_key_description('show-if-log', ['E'], 'Expand all contexts.', 'E');
  _add_key_description('show-if-theater', ['TAB'], 'Toggle between overview and focus.', 'Tab');
  _add_key_description('show-if-theater', ['SPACE'], 'Lock to a plot category or unlock.', ' ');
  _add_key_description('show-if-theater', ['LEFT'], 'Show the next plot.', 'ArrowLeft');
  _add_key_description('show-if-theater', ['RIGHT'], 'Show the previous plot.', 'ArrowRight');
  _add_key_description('show-if-theater', ['Q'], 'Open the log at the current plot.', 'Q');
  _add_key_description('show-if-theater', ['ESC'], 'Go back.', 'Escape');

  var bar = document.getElementById('bar');
  // labels, only one is visible at a time
  document.getElementById('text').appendChild(create_element('div', {id: 'theater-label', 'class': 'show-if-theater hide-if-droppeddown button label', title: 'exit theater and open log here', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); theater._open_log();}}}));
  document.getElementById('text').appendChild(create_element('div', {'class': 'show-if-droppeddown label'}, 'keyboard shortcuts'));
  // log level indicator, visible in log mode
  bar.appendChild(create_element('div', {'class': 'show-if-log icon small-icon-container', id: 'log-level-indicator'}));
  // category lock button, visible in theater mode
  bar.appendChild(create_lock({'class': 'show-if-theater button icon lock', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); theater.toggle_locked(); }}}));
  // hamburger
  bar.appendChild(create_element('div', {'class': 'hamburger icon button', events: {click: ev => { document.body.classList.toggle('droppeddown'); ev.stopPropagation(); ev.preventDefault(); }}}, create_element('div'), create_element('div'), create_element('div')));

  var header = document.getElementById('header');
  header.appendChild(create_element('div', {'class': 'dropdown', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); }}}, grid));

  window.addEventListener('keydown', keydown_handler);
  window.addEventListener('popstate', ev => apply_state(ev.state || {}));
  window.addEventListener('resize', ev => window.requestAnimationFrame(theater._update_overview_layout.bind(theater)));

  window.theater = new Theater();
  window.log = new Log();
  document.body.appendChild(theater.root);
  document.body.appendChild(create_element('div', {'class': 'dropdown-catchall', events: {click: ev => { document.body.classList.remove('droppeddown'); ev.stopPropagation(); ev.preventDefault(); }}}));

  const state = window.history.state || {};
  window.log.init_elements((state.log || {}).collapsed || {});
  if (state.log && Number.isInteger(state.log.loglevel))
    log.loglevel = state.log.loglevel;
  else
    log.loglevel = LEVELS.indexOf('info');
  apply_state(state);
  state_control = 'enabled';
});
'''

FAVICON = 'data:image/png;base64,' \
  'iVBORw0KGgoAAAANSUhEUgAAANIAAADSAgMAAABC93bRAAAACVBMVEUAAGcAAAD////NzL25' \
  'AAAAAXRSTlMAQObYZgAAAFtJREFUaN7t2SEOACEMRcEa7ofh/ldBsJJAS1bO86Ob/MZY9ViN' \
  'TD0oiqIo6qrOURRFUVRepQ4TRVEURdXVV6MoiqKoV2UJpCiKov7+p1AURVFUWZWiKIqiqI2a' \
  '8O8qJ0n+GP4AAAAASUVORK5CYII='

# vim:sw=2:sts=2:et
