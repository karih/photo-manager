app.directive('pagination', function() {
	return {
		restrict: "E",
		replace: true,
		scope: {
			switchPage: '=switchPage',
			hits: '=?',
			items: '=',
			offset: '=',
			limit: '=',
			maxRecords: '=',
		},
		controller: function($scope) { 
			var near=3;
			var update_scope = function() {
				//console.log("Updating paginator, offset=", $scope.offset, ", limit=", $scope.limit, ", count=", $scope.items.length, ", hits=", $scope.hits, ", ", $scope.maxRecords);
				$scope.disablePrevious = ($scope.offset == 0);
				$scope.previous_offset = Math.max(0, $scope.offset - $scope.limit);
				$scope.next_offset = $scope.offset + $scope.limit;

				//console.log("XX", $scope.next_offset + $scope.limit, "Y", $scope.maxRecords); 
				if (angular.isDefined($scope.maxRecords) && ($scope.next_offset + $scope.limit > $scope.maxRecords)) {
					//console.log("A");
					$scope.disableNext = true;
				} else if (angular.isDefined($scope.hits)) {
					//console.log("B");
					$scope.disableNext = ($scope.hits <= $scope.offset + $scope.limit);
				} else {
					//console.log("C");
					$scope.disableNext = $scope.items.length < $scope.limit;
				}
				//$scope.disableNext = (angular.isDefined($scope.hits) ? ) ? true : ($scope.next_offset + $scope.limit > $scope.maxRecords);
				//$scope.disableNext = true;

				$scope.current_page = Math.floor($scope.offset / $scope.limit) + 1;
				
				var last_page = Math.floor($scope.hits / $scope.limit) + 1;

				var pgs = new Set()
				pgs.add($scope.current_page);
				for (var i=0; i < near; i++) {
					pgs.add(Math.min(1+i, last_page));
					pgs.add(Math.max(1, last_page-i));

					pgs.add(Math.min($scope.current_page + i, last_page));
					pgs.add(Math.max($scope.current_page - i, 1));
				}

				$scope.pages = []	
				if (angular.isDefined($scope.hits)) {
					for (var i=1 ; i <= last_page; i++) {
						if (pgs.has(i)) {
							//console.log("Page", i, "disabled", $scope.limit*i, "max", $scope.maxRecords);
							$scope.pages.push({
								seq: true, 
								page: i, 
								current: $scope.current_page == i, 
								offset: $scope.limit*(i-1), 
								first: i == 1, 
								last: i == last_page, 
								disabled: $scope.limit*i > $scope.maxRecords
							});
						} else if ($scope.pages[$scope.pages.length-1].seq == true) {
							$scope.pages.push({seq: false});
						}
					}
				}
			}

			// XXX: This is probably a bit excessive..
			$scope.$watch('hits', update_scope);
			$scope.$watch('offset', update_scope);
			$scope.$watch('limit', update_scope);
			$scope.$watch('items', update_scope);
				
		},
		templateUrl: "/static/partials/common/pagination.html"
	}
});


app.directive('typeahead', ['$timeout', '$compile', function($timeout, $compile) {
	function setCaretPosition(elem, caretPos) {
		// stolen verbatim from somewhere on stackexchange 
		if (elem !== null) {
			if (elem.createTextRange) {
				var range = elem.createTextRange();
				range.move('character', caretPos);
				range.select();
			} else {
				if (elem.setSelectionRange) {
					elem.focus();
					elem.setSelectionRange(caretPos, caretPos);
				} else {
					elem.focus();
				}
			}
		}
	}

	return {
		restrict: "A",
		transclude: true,
		scope: {
			value: "=",
			valid: "=",
			query: "=ngModel",
			queryFunction: "=",
			template: "@?",
			multiLevel: "=?",
		},
		controller: function($scope) {
			if (angular.isUndefined($scope.template))
				$scope.template = "{{ item.value }}";
			if (angular.isUndefined($scope.multiLevel))
				$scope.multiLevel = false;
		},
		link: function(scope, element, attrs) {
			//console.log("link", scope.template);
			var template = "<span class='glyphicon form-control-feedback' ng-class='{ \"glyphicon-ok\": valid, \"glyphicon-remove\" : !valid }'></span><ul ng-show='active' class='dropdown'><ul class='dropdown-menu'><li ng-show='!searching' ng-repeat='item in candidates' style='cursor: pointer' ng-class='{active: selected == $index }' ng-mouseenter='mouseenter($index)' ng-mousedown='select($event, $index)'>" + scope.template + "</li><li ng-show='candidates.length < 1 && !searching'><em>no results</em></li><li ng-show='searching'><em>(searching)</em></li></ul></div>";
			scope.active = false;
			scope.candidates = [];
			scope.searching = false;
			scope.selected = null;
			scope.madeChoice = false;

			scope.select = function($event, index) {
				//console.log("typeahead.select(", $event, ", ", index, ")");
				//console.log("selecting ", scope.candidates[index].value);
				scope.query = scope.candidates[index].value;
				setCaretPosition(element[0], scope.query.length);
				if ($event.type == "mousedown") {
					// we are about to lose focus()
					scope.madeChoice = true; // prevent defocusing later on
				} else if ($event.type == "keydown") {
					// nothing to do
					scope.$apply();
				}

				if (scope.multiLevel === false) {
					// we have made our final choice
					//console.log("deactivating");
					scope.active = false;
				} else {
					//console.log("activating");
					scope.active = true;
				}
			}

			scope.mouseenter = function(index) {
				//console.log("mouseenter", index);
				scope.selected = index;
			}

			element.bind("keydown", function($event) {
				//console.log("typeahead.keydown(", $event, ")");
				if ($event.key == "Shift") {
					scope.value = scope.value + "X";
					scope.$apply();
				} else if ($event.key == "Tab") {
					if (scope.candidates.length == 1) {
						//console.log("we have one candidate");
						scope.select($event, 0);
					} else if (scope.selected !== null) {
						//console.log("we have more than one candidate");
						scope.select($event, scope.selected);
					} else {
						scope.active = true;
						scope.search();
					}
					$event.preventDefault();
				} else if ($event.key == "ArrowDown" && scope.candidates.length > 0) {
					scope.selected = (scope.selected == null) ? 0 : (scope.selected + 1) % scope.candidates.length;
					scope.$apply();
				} else if ($event.key == "ArrowUp" && scope.candidates.length > 0) {
					scope.selected = (scope.selected == null) ? scope.candidates.length-1 : (scope.selected - 1) % scope.candidates.length;
					scope.$apply();
				}	else if ($event.key == "Enter") {
					if (scope.valid) {
						//console.log("typeahead.keydown - valid choice");
						scope.active = false;
						scope.value = scope.query;
						scope.$apply();
					} else {
						//console.log("typeahead.keydown - invalid choice");
					}
				} else {
					// some other key was hit
					scope.active = true; 	
				}
			});

			element.bind("focus", function($event) {
				//console.log("typeahead.focus(", $event, ")");
			});

			element.bind("blur", function($event) {
				//console.log("typeahead.blur(", $event, ", madeChoice=", scope.madeChoice, ")");
				if (scope.madeChoice === true) {
					scope.madeChoice = false;
					$event.stopPropagation();
					element[0].focus();
				} else {
					scope.query = scope.value; // reset field on losing focus
					$timeout(function() {
						//console.log("blur event", $event);
						scope.active = false;
						scope.selected = null;
					}, 100);
				}
			});	

			scope.$watch('active', function(new_active) {
				//console.log("active", new_active);
			}, true);

			scope.$watch('query', function(new_query) {
				//console.log("typeahead.$watch('query', ", new_query, ")");
				if (new_query === "" || new_query === null) {
					scope.query = "";
					scope.valid = true;
					scope.candidates.length = 0;
				} else{
					scope.search();
				}
			});

			scope.search = function() {
				//console.log("typeahead.search(", scope.query, ")");

				scope.searching = true;
				scope.queryFunction(scope.query, function(res) {
					var prevlen = scope.candidates.length;
					scope.candidates.length = 0;
					angular.forEach(res.buckets, function(val) {
						scope.candidates.push(val);
					});
					if (scope.candidates.length != prevlen)
						scope.selected = null;
					scope.valid = res.valid || scope.query === "" || scope.query == null;
					scope.searching = false;
				});
			};

			scope.$watch('value', function(new_query) {
				//console.log("typeahead.$watch('value', ", new_query, ")");
				scope.query = new_query;
			});

			element.after($compile(template)(scope));
		},
	}
}]);
