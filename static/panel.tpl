<header class="slidePanel-header">
  <div class="slidePanel-actions" aria-label="actions" role="group">
    <button type="button" class="btn btn-pure btn-inverse slidePanel-close actions-top icon md-close"
      aria-hidden="true"></button>
    <div class="btn-group actions-bottom btn-group-flat" role="group">
      <button type="button" class="btn btn-pure btn-inverse icon md-chevron-left" aria-hidden="true"></button>
      <button type="button" class="btn btn-pure btn-inverse icon md-chevron-right" aria-hidden="true"></button>
    </div>
  </div>
  <h1>Titudin venenatis ipsum ac feugiat. Vestibulum ullamcorper Neque quam.</h1>
</header>
<div class="slidePanel-inner">
  <section class="slidePanel-inner-section">
    <div class="forum-header">
      <a class="avatar" href="javascript:void(0)">
        <img src="{{ url_for('static', filename='global')}}/portraits/2.jpg" alt="...">
      </a>
      <span class="name">Seevisual</span>
      <span class="time">3 minutes ago</span>
    </div>
    <div class="forum-content">
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi id neque quam.
        Aliquam sollicitudin venenatis ipsum ac feugiat. Vestibulum ullamcorper
        sodales nisi nec condimentum. Mauris convallis mauris at pellentesque volutpat.
        Phasellus at ultricies neque, quis malesuada augue. Donec eleifend condimentum
        nisl eu consectetur. Integer eleifend, nisl venenatis consequat iaculis,
        lectus arcu malesuada sem, dapibus porta quam lacus eu neque.Lorem ipsum
        dolor sit amet, consectetur adipiscing elit. </p>
      <p>Morbi id neque quam. Aliquam sollicitudin venenatis ipsum ac feugiat. Vestibulum
        ullamcorper sodales nisi nec condimentum. Mauris convallis mauris at pellentesque
        volutpat. Phasellus at ultricies neque, quis malesuada augue. Donec eleifend
        condimentum nisl eu consectetur. Integer eleifend, nisl venenatis consequat
        iaculis, lectus arcu malesuada sem, dapibus porta quam lacus eu neque.</p>
    </div>
    <div class="forum-metas">
      <div class="button-group tags">
        Tags:
        <a href="javascript: void(0)" class="badge badge-outline badge-default">Blog</a>
        <a href="javascript: void(0)" class="badge badge-outline badge-default">Design</a>
        <a href="javascript: void(0)" class="badge badge-outline badge-default">Cool</a>
      </div>
      <div class="float-right">
        <button type="button" class="btn btn-icon btn-pure btn-default">
          <i class="icon md-thumb-up" aria-hidden="true"></i>
          <span class="num">2</span>
        </button>
      </div>
      <div class="button-group share">
        Share:
        <button type="button" class="btn btn-icon btn-pure btn-default"><i class="icon bd-twitter" aria-hidden="true"></i></button>
        <button type="button" class="btn btn-icon btn-pure btn-default"><i class="icon bd-facebook" aria-hidden="true"></i></button>
        <button type="button" class="btn btn-icon btn-pure btn-default"><i class="icon bd-dribbble" aria-hidden="true"></i></button>
      </div>
    </div>
  </section>
  <section class="slidePanel-inner-section">
    <div class="forum-header">
      <div class="float-right">#
        <span class="floor">1</span>
      </div>
      <a class="avatar" href="javascript:void(0)">
        <img src="{{ url_for('static', filename='global')}}/portraits/2.jpg" alt="...">
      </a>
      <span class="name">Seevisual</span>
      <span class="time">2 minutes ago</span>
    </div>
    <div class="forum-content">
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi id neque quam.
        Aliquam sollicitudin venenatis ipsum ac feugiat. Vestibulum ullamcorper
        sodales nisi nec condimentum. </p>
      <div class="float-right">
        <button type="button" class="btn btn-icon btn-pure btn-default">
          <i class="icon md-thumb-up" aria-hidden="true"></i>
          <span class="num">2</span>
        </button>
      </div>
    </div>
  </section>
  <div class="slidePanel-comment">
    <textarea class="maxlength-textarea form-control mb-sm mb-20" rows="4"></textarea>
    <button class="btn btn-primary" data-dismiss="modal" type="button">Reply</button>
  </div>
</div>