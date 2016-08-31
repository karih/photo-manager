app.directive('pagination', function() {
	return {
		restrict: "E",
		replace: true,
		scope: {
			changePage: '=changeFunction',
			hits: '=?',
			items: '=',
			offset: '=',
			limit: '=',
		},
		controller: function($scope) { 
			var near=3;
			var update_scope = function() {
				console.log("Updating paginator, offset=", $scope.offset, ", limit=", $scope.limit, ", count=", $scope.items.length, ", hits=", $scope.hits);
				$scope.disableNext = angular.isDefined($scope.hits) ? ($scope.hits <= $scope.offset + $scope.limit) : ($scope.items.length < $scope.limit);
				$scope.disablePrevious = ($scope.offset == 0);
				$scope.previous_offset = Math.max(0, $scope.offset - $scope.limit);
				$scope.next_offset = $scope.offset + $scope.limit;

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

				//console.log(pgs);


				$scope.pages = []	
				if (angular.isDefined($scope.hits)) {
					for (var i=1 ; i <= last_page; i++) {
						if (pgs.has(i)) {
							$scope.pages.push({seq: true, page: i, current: $scope.current_page == i, offset: $scope.limit*(i-1), first: i == 1, last: i == last_page});
						} else if ($scope.pages[$scope.pages.length-1].seq == true) {
							$scope.pages.push({seq: false});
						}
					}
				}
			}

			$scope.$watch('hits', update_scope);
			$scope.$watch('offset', update_scope);
			$scope.$watch('limit', update_scope);
			$scope.$watch('items', update_scope);
				
		},
		templateUrl: "/static/partials/common/pagination.html"
	}
});


app.directive('facet', function() {
	return {
		restrict: "E",
		replace: true,
		scope: { 
			name: "@", 
			options: "=",
			filter: "&"
		},
		controller: function($scope) {
			console.log("Controller", $scope.filter);

		},
		templateUrl: "/static/partials/common/facet.html"
	}
});

app.directive('thumbnail-view', function() {
	return {}
});
