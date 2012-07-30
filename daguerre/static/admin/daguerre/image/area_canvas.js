(function($){
	var areaCanvas = window.areaCanvas = {
		keyDowns: 0,
		maxHeight: 400,
		maxWidth: 800,
		activeFuzz: 10
	};
	
	areaCanvas.Area = function(id, x1, y1, x2, y2, name, priority, del){
		var area = this,
			numeric = $([x1, y1, x2, y2, priority]);
		area.id = id;
		area.x1 = x1;
		area.y1 = y1;
		area.x2 = x2;
		area.y2 = y2;
		area.name = name;
		area.priority = priority;
		area.del = del
		
		area.getVals = function(){
			this.oldvals = this.vals
			this.vals = {
				x1: Math.floor(areaCanvas.canvasX(this.x1.value)),
				y1: Math.floor(areaCanvas.canvasY(this.y1.value)),
				x2: Math.floor(areaCanvas.canvasX(this.x2.value)),
				y2: Math.floor(areaCanvas.canvasY(this.y2.value)),
				priority: this.priority.value * 1
			}
		};
		area.setVal = function(ele, val){
			var lower = ele.lowerBound(),
				upper = ele.upperBound();
			if (val < lower) val = lower;
			if (val > upper) val = upper;
			ele.value = val;
		};
		
		numeric.attr('autocomplete', 'off')
		numeric.keydown(function(e){
			if (e.keyCode == 38 || e.keyCode == 40) {
				var inc = areaCanvas.keyDowns < 5 ? 1 : Math.floor(Math.pow(areaCanvas.keyDowns / 5, 2)),
					val;
				if(e.keyCode == 38) {
					val = this.value * 1 + inc;
				} else if(e.keyCode == 40) {
					val = this.value - inc;
				}
				area.setVal(this, val);
				areaCanvas.keyDowns++;
			} else if (e.keyCode == 13) {
				area.setVal(this, this.value);
				e.preventDefault();
			};
			if (e.keyCode == 38 || e.keyCode == 40 || e.keyCode == 13) {
				if (this == area.priority) {
					area.getVals();
					areaCanvas.redraw(area.vals.x1, area.vals.y1, area.vals.x2, area.vals.y2);
				} else {
					area.resize();
				}
			}
		});
		numeric.keyup(function(e){
			areaCanvas.keyDowns = 0;
		});
		numeric.blur(function(){
			area.setVal(this, this.value);
			if (this == area.priority) {
				area.getVals();
				areaCanvas.redraw(area.vals.x1, area.vals.y1, area.vals.x2, area.vals.y2);
			} else {
				area.resize();
			}
		});
		priority.lowerBound = function(){return 1;};
		priority.upperBound = function(){return this.value * 1 + 1;};
		// Bound by the opposite coordinate (or the opposite edge of the image if that's not available.)
		x1.lowerBound = function(){return 0;};
		x1.upperBound = function(){return (area.x2.value == "" ? areaCanvas.img.width : area.x2.value * 1) - 1;};
		x2.lowerBound = function(){return area.x1.value * 1 + 1;};
		x2.upperBound = function(){return areaCanvas.img.width;};
		y1.lowerBound = function(){return 0;};
		y1.upperBound = function(){return (area.y2.value == "" ? areaCanvas.img.height : area.y2.value * 1) - 1;};
		y2.lowerBound = function(){return area.y1.value * 1 + 1;};
		y2.upperBound = function(){return areaCanvas.img.height;};
		
		area.draw = function(x1, y1, x2, y2){
			// Refetch the width, height, etc. and then draw the box delimited by
			// the passed-in corners (or the entire area if none were passed.)
			// The dimensions passed in are canvas dimensions, not image dimensions.
			if (!this.del.checked && this.overlaps(x1, y1, x2, y2)) {
				var context = areaCanvas.context,
					color,
					alpha = 0.4,
					x1 = Math.max(this.vals.x1, x1 || 0),
					y1 = Math.max(this.vals.y1, y1 || 0),
					x2 = Math.min(this.vals.x2, x2 || areaCanvas.ele.width),
					y2 = Math.min(this.vals.y2, y2 || areaCanvas.ele.height),
					width = x2 - x1,
					height = y2 - y1,
					priority = this.vals.priority;
				
				switch(priority){
					case 1:
						color = "rgba(0,255,0," + alpha + ")";
						break;
					case 2:
						color = "rgba(150, 150, 255," + alpha + ")";
						break;
					case 3:
						color = "rgba(225, 225, 125," + alpha + ")";
						break;
					default:
						color = "rgba(200, 200, 200," + alpha + ")";
				}
				context.fillStyle = color;
				context.fillRect(x1, y1, width, height);
				
				context.beginPath();
				
				if (x1 == this.vals.x1){
					var x = x1 + .5;
					context.moveTo(x, y1);
					context.lineTo(x, y2);
				};
				if (x2 == this.vals.x2){
					var x = x2 - .5;
					context.moveTo(x, y1);
					context.lineTo(x, y2);
				};
				if (y1 == this.vals.y1){
					var y = y1 + .5;
					context.moveTo(x1, y);
					context.lineTo(x2, y);
				};
				if (y2 == this.vals.y2){
					var y = y2 - .5;
					context.moveTo(x1, y);
					context.lineTo(x2, y);
				};
				
				context.stroke();
				context.closePath();
			};
		};
		area.resize = function(){
			this.getVals();
			
			var dx1 = this.vals.x1 - this.oldvals.x1,
				dy1 = this.vals.y1 - this.oldvals.y1,
				dx2 = this.vals.x2 - this.oldvals.x2,
				dy2 = this.vals.y2 - this.oldvals.y2;
			
			if (dx1 != 0 || dx2 != 0) {
				var by1 = this.oldvals.y1,
					by2 = this.oldvals.y2;
				
				if (dx1 < 0) {
					// Grow left
					var bx1 = this.vals.x1,
						bx2 = this.oldvals.x1 + 1;
				} else if (dx1 > 0){
					// Shrink right
					var bx1 = this.oldvals.x1,
						bx2 = this.vals.x1;
				}
				if (dx2 > 0) {
					// Grow right
					var bx1 = this.oldvals.x2 - 1,
						bx2 = this.vals.x2;
				} else if (dx2 < 0){
					// Shrink left
					var bx1 = this.vals.x2,
						bx2 = this.oldvals.x2;
				}
				areaCanvas.redraw(bx1, by1, bx2, by2);
			}
			if (dy1 != 0 || dy2 != 0) {
				var bx1 = this.vals.x1,
					bx2 = this.vals.x2;
				
				if (dy1 < 0) {
					// Grow up
					var by1 = this.vals.y1,
						by2 = this.oldvals.y1 + 1;
				} else if (dy1 > 0) {
					// Shrink down
					var by1 = this.oldvals.y1,
						by2 = this.vals.y1;
				}
				if (dy2 > 0) {
					// Grow down
					var by1 = this.oldvals.y2 - 1,
						by2 = this.vals.y2;
				} else if (dy2 < 0) {
					// Shrink up
					var by1 = this.vals.y2,
						by2 = this.oldvals.y2;
				}
				areaCanvas.redraw(bx1, by1, bx2, by2);
			}
		};
		area.overlaps = function(x1, y1, x2, y2){
			// Returns true if the area overlaps with the given box and false otherwise.
			if (x1 > this.vals.x2 || x2 < this.vals.x1) return false;
			if (y1 > this.vals.y2 || y2 < this.vals.y1) return false;
			return true;
		};
		area.active = function(x, y){
			// Given an x/y position in the canvas, returns false if the area is not active
			// or otherwise an object with x, y, and area properties. May return null for
			// x or y if only one direction is actively draggable.
			var fuzz = areaCanvas.activeFuzz;
			
			if (x > this.vals.x2 + fuzz || x < this.vals.x1 - fuzz) return false;
			if (y > this.vals.y2 + fuzz || y < this.vals.y1 - fuzz) return false;
			
			var area = this,
				ax = null,
				ay = null;
			
			if (this.isActiveEle(x, "x1", "x2")) {
				ax = this.x1;
			} else if (this.isActiveEle(x, "x2", "x1")) {
				ax = this.x2;
			}
			if (this.isActiveEle(y, "y1", "y2")) {
				ay = this.y1;
			} else if (this.isActiveEle(y, "y2", "y1")) {
				ay = this.y2;
			}
			return {area: this, x: ax, y: ay};
		};
		area.isActiveEle = function(val, name, oppname) {
			var thisval = this.vals[name],
				oppval = this.vals[oppname];
			if (oppval < thisval && val < oppval) return false;
			if (oppval > thisval && val > oppval) return false;
			return (val > thisval - areaCanvas.activeFuzz && val < thisval + areaCanvas.activeFuzz)
		};
	};
	
	areaCanvas.setUp = function(){
		var ele = areaCanvas.ele = document.getElementById('areaCanvas'),
			context = areaCanvas.context = ele.getContext("2d"),
			img = areaCanvas.img = new Image(),
			areas = areaCanvas.areas = [];
		
		areaCanvas.addButton = $('#areas-group .add-handler').eq(0);
		
		tools = $('<ul class="tools"><li></li></ul>')
		$('li', tools).append(areaCanvas.redrawButton);
		$('#areas-group h2').eq(0).after(tools);
		
		img.onload = function(){
			var width = img.width,
				height = img.height,
				ratio = width / height;
			if (areaCanvas.maxHeight < height) {
				height = areaCanvas.maxHeight;
				width = height * ratio;
			}
			if (areaCanvas.maxWidth < width) {
				width = areaCanvas.maxWidth;
				height = width / ratio;
			}
			ele.width = Math.floor(width);
			ele.height = Math.floor(height);
			areaCanvas.draw();
		}
		img.src = ele.getAttribute('data-src');
		
		var el = $(ele),
			body = $(document.body);
		
		// Set mouse movement handling.
		el.mousedown(function(e){
			var pos = areaCanvas.getCursorPosition(e),
				active;
			
			for(var i=0;i<areas.length;i++){
				active = areas[i].active(pos.x, pos.y);
				if (active) break;
			}
			if(active){
				// Mousedown triggers 'drag' or 'move' mode.
				if (active.x || active.y) {
					var mousemoveCallback = function(e){
						var pos = areaCanvas.getCursorPosition(e),
							area = active.area;
						if (active.x) area.setVal(active.x, Math.floor(areaCanvas.imgX(pos.x)));
						if (active.y) area.setVal(active.y, Math.floor(areaCanvas.imgY(pos.y)));
						active.area.resize();
					}
				} else {
					active.offset = {x: pos.x - active.area.vals.x1, y: pos.y - active.area.vals.y1}
					var mousemoveCallback = function(e){
						var pos = areaCanvas.getCursorPosition(e),
							area = active.area,
							offset = active.offset,
							x1 = pos.x - offset.x,
							y1 = pos.y - offset.y,
							imgX1 = Math.floor(areaCanvas.imgX(x1)),
							imgY1 = Math.floor(areaCanvas.imgY(y1)),
							width = area.x2.value - area.x1.value,
							height = area.y2.value - area.y1.value,
							img = areaCanvas.img;
						
						area.setVal(area.x1, Math.min(imgX1, img.width - width));
						area.setVal(area.y1, Math.min(imgY1, img.height - height));
						area.resize();
						area.setVal(area.x2, area.x1.value * 1 + width);
						area.setVal(area.y2, area.y1.value * 1 + height);
						area.resize();
					}
				}
				
				body.mousemove(mousemoveCallback);
				el.unbind('mousemove', areaCanvas.setResizeCursor);
				body.mouseup(function mouseupCallback(){
					body.unbind('mouseup', mouseupCallback);
					body.unbind('mousemove', mousemoveCallback);
					el.mousemove(areaCanvas.setResizeCursor);
				});
			} else {
				// Mousedown triggers 'new area' mode.
				var startpos = {x: pos.x, y: pos.y}
				body.mouseup(function mouseupCallback(e){
					body.unbind('mouseup', mouseupCallback);
					areaCanvas.addButton.click();
					var pos = areaCanvas.getCursorPosition(e),
						x1 = Math.min(startpos.x, pos.x),
						x2 = Math.max(startpos.x, pos.x),
						y1 = Math.min(startpos.y, pos.y),
						y2 = Math.max(startpos.y, pos.y),
						imgX1 = Math.floor(areaCanvas.imgX(x1)),
						imgX2 = Math.floor(areaCanvas.imgX(x2)),
						imgY1 = Math.floor(areaCanvas.imgY(y1)),
						imgY2 = Math.floor(areaCanvas.imgY(y2)),
						area = areaCanvas.areas.pop();
					
					areaCanvas.areas.push(area);
					
					area.setVal(area.x1, imgX1);
					area.setVal(area.y1, imgY1);
					area.setVal(area.x2, imgX2);
					area.setVal(area.y2, imgY2);
					
					area.getVals();
					
					areaCanvas.redraw(area.vals.x1, area.vals.y1, area.vals.x2, area.vals.y2);
				})
			}
		});
		el.mousemove(areaCanvas.setResizeCursor);
		el.mousedown(areaCanvas.setResizeCursor);
	};
	areaCanvas.setResizeCursor = function(e){
		var pos = areaCanvas.getCursorPosition(e),
			fuzz = areaCanvas.activeFuzz,
			ele = areaCanvas.ele,
			areas = areaCanvas.areas,
			n, e, s, w, area, c;
	
		ele.style.cursor = "crosshair";
	
		for(var i=areas.length-1;i>-1;i--){
			area = areas[i];
			if (pos.x > area.vals.x2 + fuzz || pos.x < area.vals.x1 - fuzz) continue;
			if (pos.y > area.vals.y2 + fuzz || pos.y < area.vals.y1 - fuzz) continue;
			c = null;
			n = area.isActiveEle(pos.y, "y1", "y2");
			s = area.isActiveEle(pos.y, "y2", "y1");
			w = area.isActiveEle(pos.x, "x1", "x2");
			e = area.isActiveEle(pos.x, "x2", "x1");
			if(n && w) {c = "nw";}
			else if (n && e) {c = "ne";}
			else if (s && e) {c = "se";}
			else if (s && w) {c = "sw";}
			else if (n) {c = "n";}
			else if (e) {c = "e";}
			else if (s) {c = "s";}
			else if (w) {c = "w";}
			if (c) {
				ele.style.cursor = c + "-resize";
			} else {
				ele.style.cursor = "move"
			}
		}
	};
	
	areaCanvas.draw = function(){
		var context = areaCanvas.context,
			ele = areaCanvas.ele,
			img = areaCanvas.img,
			areas = areaCanvas.areas;
		ele.width = ele.width;
		
		// Draw the image.
		context.drawImage(img, 0, 0, ele.width, ele.height);
		
		for(var i=0;i<areas.length;i++){
			areas[i].getVals();
		}
		
		// Draw the areas
		areaCanvas.drawAreas(0, 0, ele.width, ele.height);
	};
	areaCanvas.drawAreas = function(x1, y1, x2, y2){
		// Draw the areas within the defined box according to their layers.
		for(var i=0;i<this.areas.length;i++){
			this.areas[i].draw(x1, y1, x2, y2);
		}
	}
	areaCanvas.erase = function(x1, y1, x2, y2){
		// Erase the area bounded by the input coordinates. These are canvas coordinates,
		// not image coordinates.
		var img = areaCanvas.img,
			context = areaCanvas.context,
			areas = areaCanvas.areas
			dw = x2 - x1,
			dh = y2 - y1,
			sx1 = areaCanvas.imgX(x1),
			sy1 = areaCanvas.imgY(y1),
			sx2 = areaCanvas.imgX(x2),
			sy2 = areaCanvas.imgY(y2),
			sw = sx2 - sx1,
			sh = sy2 - sy1;
		
		context.drawImage(img, sx1, sy1, sw, sh, x1, y1, dw, dh);
	};
	areaCanvas.redraw = function(x1, y1, x2, y2){
		areaCanvas.erase(x1, y1, x2, y2);
		areaCanvas.drawAreas(x1, y1, x2, y2);
	}
	
	areaCanvas.addFormArea = function(form){
		var id = form[0].id.slice(5),
			areas = areaCanvas.areas,
			x1 = document.getElementById('id_areas-' + id + "-x1");
		if (!x1) return null;
		
		var y1 = document.getElementById('id_areas-' + id + "-y1"),
			x2 = document.getElementById('id_areas-' + id + "-x2"),
			y2 = document.getElementById('id_areas-' + id + "-y2"),
			name = document.getElementById('id_areas-' + id + "-name"),
			priority = document.getElementById('id_areas-' + id + "-priority"),
			del = document.getElementById('id_areas-' + id + "-DELETE");
		
		var area = new areaCanvas.Area(id, x1, y1, x2, y2, name, priority, del);
		form[0].area = area
		areas.push(area);
		return area;
	};
	areaCanvas.removeFormArea = function(form){
		var areas = this.areas,
			area = form[0].area;
		
		for(var i=0;i<areas.length;i++){
			if(areas[i] == area) {
				areas.splice(i, 1);
				break;
			};
		};
		areaCanvas.redraw(area.vals.x1, area.vals.y1, area.vals.x2, area.vals.y2);
	};
	
	areaCanvas.moveToTop = function(area){
		var idx = $.inArray(area, areaCanvas.areas);
		if (idx != -1) {
			var area = areaCanvas.areas.splice(idx, 1)[0];
			areaCanvas.areas.push(area);
		}
	}
	
	areaCanvas.getCursorPosition = function(e) {
		var x, y,
			ele = areaCanvas.ele,
			xScale = ele.width / ele.offsetWidth,
			yScale = ele.height / ele.offsetHeight;
		if (e.pageX != undefined && e.pageY != undefined){
			x = e.pageX;
			y = e.pageY;
		} else {
			x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
			y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
		}
		var parent = ele;
		while (parent) {
			x -= parent.offsetLeft;
			y -= parent.offsetTop;
			parent = parent.offsetParent;
		}
		return {x: x, y: y};
	};
	
	areaCanvas.imgX = function(x) {
		// Takes an x on the canvas element and translates it to an x on the original image.
		var ele = areaCanvas.ele,
			img = areaCanvas.img,
			xScale = img.width / ele.offsetWidth,
			yScale = img.height / ele.offsetHeight;
		
		return x * xScale;
	};
	areaCanvas.imgY = function(y) {
		// Takes a y on the canvas element and translates it to a y on the original image.
		var ele = areaCanvas.ele,
			img = areaCanvas.img,
			yScale = img.height / ele.offsetHeight;
		
		return y * yScale;
	};
	areaCanvas.canvasX = function(x) {
		// Takes an x on the original image and translates it to an x on the canvas element.
		var ele = areaCanvas.ele,
			img = areaCanvas.img,
			xScale = img.width / ele.offsetWidth,
			yScale = img.height / ele.offsetHeight;
		
		return x / xScale;
	};
	areaCanvas.canvasY = function(y) {
		// Takes a y on the original image and translates it to a y on the canvas element.
		var ele = areaCanvas.ele,
			img = areaCanvas.img,
			yScale = img.height / ele.offsetHeight;
		
		return y / yScale;
	};
	
	areaCanvas.redrawButton = $('<a href=""><img src="/static/admin/daguerre/image/arrow-circle-315.png" alt="Redraw" title="Redraw" /></a>');
	areaCanvas.redrawButton.click(function(e){
		e.preventDefault();
		areaCanvas.draw();
	});
	
	$(areaCanvas.setUp);
}(django.jQuery));